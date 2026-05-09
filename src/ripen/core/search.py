import asyncio
import datetime
import json
import re

from ripen.common.utils import (
    batch_cosine_similarity,
    calculate_importance,
    escape_fts5_query,
    get_logger,
    log_error,
)
from ripen.core.bank import read_bank_data
from ripen.core.graph import get_graph_data
from ripen.infra.database import (
    async_get_connection,
    async_get_thoughts_connection,
    log_search_stat,
    update_access,
)
from ripen.infra.embeddings import compute_embedding
from ripen.infra.llm import get_llm_provider

logger = get_logger("search")


async def perform_keyword_search(
    query: str, limit: int = 5, exclude_session_id: str = None, include_transient: bool = True
):
    """
    Improved Keyword Search Logic using FTS5 and maturity-based scoring.
    """
    async with await async_get_connection() as conn:
        query_words = re.findall(r"\w+", query.lower())
        if not query_words:
            return []

        scored_results = {}

        # 1. Search Knowledge DB using FTS5 (Entities, Observations, Bank, Troubleshooting)
        # (Source, Table, ID_Col, Content_Col, Maturity, Boost)
        fts_sources = [
            ("troubleshooting_knowledge", "troubleshooting_knowledge_fts", "id", "solution", "STABLE", 2.5),
            ("entities", "entities_fts", "name", "description", "STABLE", 1.5),
            ("observations", "observations_fts", "entity_name", "content", "STABLE", 1.2),
            ("bank_files", "bank_files_fts", "filename", "content", "OBSERVED", 1.0),
        ]

        # Escape query for FTS5 syntax
        fts_query = escape_fts5_query(query)

        for source_name, fts_table, id_col, content_col, maturity, boost in fts_sources:
            try:
                if not fts_query:
                    raise ValueError("Empty FTS query")

                cursor = await conn.execute(
                    f"SELECT {id_col}, {content_col}, bm25({fts_table}) "
                    f"FROM {fts_table} WHERE {fts_table} MATCH ?",
                    (fts_query,),
                )
                for row_id, content, rank in await cursor.fetchall():
                    score = max(0.1, abs(rank) * boost)
                    if query.lower() in str(row_id).lower():
                        score += 15.0

                    key = (source_name, row_id)
                    current_score, _, _ = scored_results.get(key, (0.0, "", ""))
                    scored_results[key] = (current_score + score, str(content), maturity)
            except Exception:
                # Fallback to LIKE search
                cursor = await conn.execute(
                    f"SELECT {id_col}, {content_col} FROM {source_name if 'fts' not in fts_table else source_name} "
                    f"WHERE ({content_col} LIKE ? OR {id_col} LIKE ?) AND (status = 'active' OR 1=1)",
                    (f"%{query}%", f"%{query}%"),
                )
                for row_id, content in await cursor.fetchall():
                    key = (source_name, row_id)
                    current_score, _, _ = scored_results.get(key, (0.0, "", ""))
                    scored_results[key] = (current_score + (2.0 * boost), str(content), maturity)

        # 1.1 Search Tags
        placeholders = ",".join(["?"] * len(query_words))
        cursor = await conn.execute(
            f"SELECT content_id, content_type, tag FROM tags WHERE tag IN ({placeholders})",
            [f"#{w}" for w in query_words],
        )
        for cid, ctype, tag in await cursor.fetchall():
            score = 15.0
            key = (ctype + "s" if not ctype.endswith("s") else ctype, cid)
            maturity = "STABLE" if ctype in ["entity", "observation", "troubleshooting"] else "OBSERVED"
            current_score, content, _ = scored_results.get(key, (0.0, f"Matched tag: {tag}", maturity))
            scored_results[key] = (current_score + score, content, maturity)

        # 2. Search Thoughts DB (Transient)
        if include_transient:
            try:
                if not fts_query:
                    raise ValueError("Empty FTS query")

                async with await async_get_thoughts_connection() as t_conn:
                    t_cursor = await t_conn.execute(
                        "SELECT session_id, thought_number, thought, bm25(thought_history_fts) "
                        "FROM thought_history_fts WHERE thought_history_fts MATCH ? "
                        "AND session_id != ?",
                        (fts_query, exclude_session_id or ""),
                    )
                    for sess_id, t_num, thought, rank in await t_cursor.fetchall():
                        score = max(0.1, abs(rank) * 0.3)
                        key = ("thought_history", f"{sess_id}#{t_num}")
                        current_score, _, _ = scored_results.get(key, (0.0, "", ""))
                        scored_results[key] = (current_score + score, str(thought), "TRANSIENT")
            except Exception as e:
                logger.debug(f"FTS5 thought search failed: {e}")

        sorted_items = sorted(scored_results.items(), key=lambda x: x[1][0], reverse=True)
        formatted_results = []
        for (source, row_id), (score, content, maturity) in sorted_items[:limit]:
            formatted_results.append(
                {
                    "source": source,
                    "id": row_id,
                    "score": round(score, 2),
                    "maturity": maturity,
                    "content": content,
                }
            )

        hit_ids = [str(r["id"]) for r in formatted_results]
        await log_search_stat(query, len(formatted_results), hit_ids=hit_ids)
        return formatted_results


async def perform_search(
    query: str, limit: int = 10, candidate_limit: int = 20, include_transient: bool = True
):
    """Hybrid search logic (Semantic + Keyword)."""
    logger.info(f"perform_search START query={query}")
    start_search = datetime.datetime.now()

    task_vector = asyncio.create_task(compute_embedding(query))
    task_keyword = asyncio.create_task(
        perform_keyword_search(query, include_transient=include_transient)
    )

    try:
        async with await async_get_connection() as conn:
            cursor = await conn.execute("""
                SELECT e.content_id, e.vector
                FROM embeddings e
                LEFT JOIN entities ent ON e.content_id = ent.name
                LEFT JOIN bank_files bf ON e.content_id = bf.filename
                WHERE (ent.status = 'active' OR bf.status = 'active')
            """)
            all_rows = await cursor.fetchall()

            query_vector = await task_vector
            keyword_results = await task_keyword

            if not query_vector or not all_rows:
                return await get_graph_data(query), await read_bank_data(query)

            all_cids = [r[0] for r in all_rows]
            all_vectors = [json.loads(r[1]) for r in all_rows]
            similarities = batch_cosine_similarity(query_vector, all_vectors)

            cursor = await conn.execute(
                "SELECT content_id, access_count, last_accessed FROM knowledge_metadata"
            )
            metadata = await cursor.fetchall()
            meta_map = {m[0]: (m[1], m[2]) for m in metadata}
            {r["id"]: r["score"] for r in keyword_results}

            results = []
            seen_cids = set()

            for i, cid in enumerate(all_cids):
                sim = float(similarities[i])
                count, last = meta_map.get(cid, (0, datetime.datetime.now().isoformat()))
                importance = calculate_importance(count, last)
                k_res = next((r for r in keyword_results if r["id"] == cid), None)
                k_score = k_res["score"] if k_res else 0.0
                
                # Maturity-based boosting
                maturity = k_res["maturity"] if k_res else "STABLE"
                maturity_boost = 1.0
                if maturity == "STABLE":
                    maturity_boost = 1.2
                elif maturity == "TRANSIENT":
                    maturity_boost = 0.5
                
                final_score = ((sim * 0.4) + (importance * 0.15) + (k_score * 0.45)) * maturity_boost
                results.append((cid, final_score))
                seen_cids.add(cid)

            for res in keyword_results:
                cid = res["id"]
                if cid not in seen_cids:
                    k_score = res["score"]
                    maturity = res["maturity"]
                    maturity_boost = 1.2 if maturity == "STABLE" else (0.5 if maturity == "TRANSIENT" else 1.0)
                    
                    count, last = meta_map.get(cid, (0, datetime.datetime.now().isoformat()))
                    importance = calculate_importance(count, last)
                    final_score = ((k_score * 0.5) + (importance * 0.5)) * maturity_boost
                    results.append((cid, final_score))

            results.sort(key=lambda x: x[1], reverse=True)
            top_results = [r for r in results[:limit] if r[1] > 0.03]
            top_cids = [r[0] for r in top_results]

            for cid in top_cids:
                await update_access(cid, conn=conn)

            graph_task = asyncio.create_task(get_graph_data_by_cids(top_cids, conn))
            bank_task = asyncio.create_task(get_bank_data_by_cids(top_cids, conn))
            graph_data, bank_data = await asyncio.gather(graph_task, bank_task)

            dur = (datetime.datetime.now() - start_search).total_seconds()
            logger.info(f"perform_search COMPLETE query={query} duration={dur:.3f}s")

            await log_search_stat(query, len(top_results), hit_ids=top_cids, conn=conn)
            return graph_data, bank_data

    except Exception as e:
        log_error(f"Search failed for query: {query}", e)
        return await get_graph_data(query), await read_bank_data(query)


async def get_graph_data_by_cids(cids: list[str], conn):
    if not cids:
        return {"entities": [], "relations": [], "observations": [], "troubleshooting": []}
    
    placeholders = ",".join(["?"] * len(cids))
    
    # 1. Fetch Entities
    cursor = await conn.execute(
        f"SELECT * FROM entities WHERE name IN ({placeholders}) AND status = 'active'", cids
    )
    entities = await cursor.fetchall()
    
    # 2. Fetch Observations
    cursor = await conn.execute(
        f"SELECT * FROM observations WHERE entity_name IN ({placeholders}) AND status = 'active'",
        cids,
    )
    obs = await cursor.fetchall()

    # 3. Fetch Troubleshooting
    # Filter CIDs that look like integers
    ts_ids = [c for c in cids if str(c).isdigit()]
    ts_rows = []
    if ts_ids:
        ts_placeholders = ",".join(["?"] * len(ts_ids))
        cursor = await conn.execute(
            f"SELECT * FROM troubleshooting_knowledge WHERE id IN ({ts_placeholders})", ts_ids
        )
        ts_rows = await cursor.fetchall()

    matched_names = [e["name"] for e in entities]
    relations = []
    if matched_names:
        p2 = ",".join(["?"] * len(matched_names))
        cursor = await conn.execute(
            f"SELECT * FROM relations WHERE (subject IN ({p2}) OR object IN ({p2})) "
            "AND status = 'active'",
            matched_names + matched_names,
        )
        relations = await cursor.fetchall()

    return {
        "entities": [dict(e) for e in entities],
        "relations": [dict(r) for r in relations],
        "observations": [
            {"entity": o["entity_name"], "content": o["content"], "at": o["timestamp"]} for o in obs
        ],
        "troubleshooting": [dict(t) for t in ts_rows],
    }


async def get_bank_data_by_cids(cids: list[str], conn):
    if not cids:
        return {}
    placeholders = ",".join(["?"] * len(cids))
    cursor = await conn.execute(
        f"SELECT filename, content FROM bank_files WHERE filename IN ({placeholders}) "
        "AND status = 'active'",
        cids,
    )
    files = await cursor.fetchall()
    return {f["filename"]: f["content"] for f in files}


async def search_memory_logic(query: str, limit: int = 10):
    """Compatibility wrapper for system tests."""
    graph_data, bank_data = await perform_search(query, limit)
    return {
        "entities": graph_data["entities"],
        "relations": graph_data["relations"],
        "observations": graph_data["observations"],
        "troubleshooting": graph_data.get("troubleshooting", []),
        "bank_files": bank_data,
    }


async def synthesize_knowledge(entity_name: str):
    """Legacy synthesis function refactored to use LlmProvider."""
    async with await async_get_connection() as conn:
        try:
            cursor = await conn.execute("SELECT * FROM entities WHERE name = ?", (entity_name,))
            entity = await cursor.fetchone()
            if not entity:
                return f"Error: Entity '{entity_name}' not found."

            cursor = await conn.execute(
                "SELECT content, timestamp FROM observations WHERE entity_name = ? "
                "AND status='active'",
                (entity_name,),
            )
            obs = await cursor.fetchall()
            cursor = await conn.execute(
                "SELECT * FROM relations WHERE (subject = ? OR object = ?) AND status='active'",
                (entity_name, entity_name),
            )
            rels = await cursor.fetchall()

            provider = get_llm_provider()
            prompt = (
                "You are a Knowledge Synthesis Engine. Summarize everything known about "
                f"'{entity_name}'.\n\n"
                f"ENTITY INFO: {entity['entity_type']} - {entity['description']}\n\n"
                f"OBSERVATIONS:\n"
                + "\n".join([f"- ({o['timestamp']}) {o['content']}" for o in obs])
                + "\n\n"
                "RELATIONS:\n"
                + "\n".join(
                    [f"- {r['subject']} --({r['predicate']})--> {r['object']}" for r in rels]
                )
            )

            system_instruction = (
                "You are a high-precision knowledge synthesis engine. "
                "Distill technical facts with absolute accuracy."
            )
            summary = await provider.generate_content(
                prompt=prompt, system_instruction=system_instruction
            )
            return summary
        except Exception as e:
            logger.error(f"Synthesis failed for {entity_name}: {e}")
            return f"Error: {e}"


async def synthesize_entity_detailed(entity_name: str, observations: list[dict]) -> str:
    """
    Synthesizes multiple observations about an entity into a coherent summary.
    Uses the configured LLM provider (Ollama or Gemini).
    """
    if not observations:
        return f"No observations found for {entity_name}."

    provider = get_llm_provider()
    prompt = f"""
    Entity: {entity_name}
    Observations:
    {json.dumps(observations, indent=2)}

    Task: Create a single, high-density technical summary of this entity based on the observations.
    Identify any conflicts or changes over time.
    Return only the summary.
    """
    system_instruction = (
        "You are a high-precision knowledge synthesis engine. "
        "Distill technical facts with absolute accuracy."
    )

    try:
        summary = await provider.generate_content(
            prompt=prompt, system_instruction=system_instruction
        )
        return summary
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return f"[Synthesis Error] {str(e)}"
