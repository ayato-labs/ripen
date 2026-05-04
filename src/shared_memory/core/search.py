import asyncio
from typing import Any

from shared_memory.common.utils import get_logger, log_error
from shared_memory.core import graph
from shared_memory.infra.database import async_get_connection, retry_on_db_lock

logger = get_logger(\"search\")


async def perform_search(query: str) -> tuple[dict[str, Any], dict[str, Any]]:
    \"\"\"
    Performs a hybrid search (FTS5 + Semantic proxy) across graph and bank.
    \"\"\"
    # 1. Graph Search
    graph_results = await search_graph(query)

    # 2. Bank Search
    bank_results = await search_bank(query)

    # Log stats for SSoT observability
    from shared_memory.infra.database import log_search_stat

    # Background log (don't wait)
    asyncio.create_task(
        log_search_stat(
            query=query,
            results_count=len(graph_results.get(\"relations\", []))
            + len(bank_results.get(\"files\", [])),
        )
    )

    return graph_results, bank_results


@retry_on_db_lock()
async def search_graph(query: str) -> dict[str, Any]:
    \"\"\"FTS5 search on the graph table.\"\"\"
    async with async_get_connection() as conn:
        cursor = await conn.cursor()
        # Use FTS5 virtual table
        await cursor.execute(
            \"\"\"
            SELECT subject, relation, object
            FROM graph_fts
            WHERE graph_fts MATCH ?
            ORDER BY rank
            LIMIT 20
            \"\"\",
            (query,),
        )
        rows = await cursor.fetchall()
        relations = [{\"subject\": r[0], \"relation\": r[1], \"object\": r[2]} for r in rows]
        return {\"relations\": relations}


@retry_on_db_lock()
async def search_bank(query: str) -> dict[str, Any]:
    \"\"\"FTS5 search on the bank table.\"\"\"
    async with async_get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            \"\"\"
            SELECT filename, content
            FROM bank_fts
            WHERE bank_fts MATCH ?
            ORDER BY rank
            LIMIT 10
            \"\"\",
            (query,),
        )
        rows = await cursor.fetchall()
        files = [{\"filename\": r[0], \"content\": r[1]} for r in rows]
        return {\"files\": files}


async def synthesize_knowledge(entity_name: str) -> str:
    \"\"\"
    Synthesizes a summary of an entity using its graph relations and bank content.
    \"\"\"
    from shared_memory.common.utils import get_gemini_client

    client = get_gemini_client()
    if not client:
        return \"Gemini client not initialized.\"

    # 1. Gather all related info
    async with async_get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            \"SELECT relation, object FROM graph WHERE subject = ?\", (entity_name,)
        )
        relations = await cursor.fetchall()

        await cursor.execute(
            \"SELECT content FROM observations WHERE entity_name = ?\", (entity_name,)
        )
        observations = await cursor.fetchall()

    if not relations and not observations:
        return f\"No direct knowledge found for '{entity_name}'.\"

    # 2. Build synthesis prompt
    context = f\"Entity: {entity_name}\\n\"
    context += \"Relations:\\n\" + \"\\n\".join([f\"- {r[0]} {r[1]}\" for r in relations])
    context += \"\\nObservations:\\n\" + \"\\n\".join([f\"- {o[0]}\" for o in observations])

    prompt = f\"\"\"Synthesize a concise, high-density technical summary of the following entity knowledge.
Context:
{context}

Summary (Markdown):\"\"\"

    try:
        response = client.models.generate_content(model=\"gemini-2.0-flash\", contents=prompt)
        return response.text
    except Exception as e:
        log_error(\"Knowledge synthesis failed\", e)
        return f\"Synthesis failed: {e}\"
