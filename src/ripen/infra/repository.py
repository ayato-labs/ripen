import json
from ripen.infra.database import async_get_connection

class BankRepository:
    """Repository for managing bank_files and related queries."""
    
    @staticmethod
    async def get_active_filenames() -> list[str]:
        async with await async_get_connection() as conn:
            cursor = await conn.execute("SELECT filename FROM bank_files WHERE status = 'active'")
            return [r[0] for r in await cursor.fetchall()]

    @staticmethod
    async def get_active_files_content() -> list[tuple[str, str]]:
        async with await async_get_connection() as conn:
            cursor = await conn.execute("SELECT filename, content FROM bank_files WHERE status = 'active'")
            return await cursor.fetchall()

    @staticmethod
    async def get_all_files_content(conn) -> list[tuple[str, str]]:
        cursor = await conn.execute("SELECT filename, content FROM bank_files")
        return await cursor.fetchall()

    @staticmethod
    async def get_file_content(conn, filename: str) -> str | None:
        cursor = await conn.execute("SELECT content FROM bank_files WHERE filename = ?", (filename,))
        row = await cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    async def upsert_bank_file(conn, filename: str, content: str, agent_id: str):
        await conn.execute(
            "INSERT OR REPLACE INTO bank_files (filename, content, updated_by) VALUES (?, ?, ?)",
            (filename, content, agent_id),
        )

    @staticmethod
    async def get_bank_files_by_names(conn, names: list[str]):
        if not names:
            return []
        placeholders = ",".join(["?"] * len(names))
        cursor = await conn.execute(
            f"SELECT filename, content FROM bank_files WHERE filename IN ({placeholders}) "
            "AND status = 'active'",
            names,
        )
        return await cursor.fetchall()

class AuditRepository:
    """Repository for managing audit logs."""
    
    @staticmethod
    async def log_action(conn, table_name: str, content_id: str, action: str, old_data: str | None, new_data: str, agent_id: str, meta_data: str | None = None):
        if meta_data:
            await conn.execute(
                "INSERT INTO audit_logs (table_name, content_id, action, old_data, new_data, agent_id, meta_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (table_name, content_id, action, old_data, new_data, agent_id, meta_data),
            )
        else:
            await conn.execute(
                "INSERT INTO audit_logs (table_name, content_id, action, old_data, new_data, agent_id) VALUES (?, ?, ?, ?, ?, ?)",
                (table_name, content_id, action, old_data, new_data, agent_id),
            )

class EntityRepository:
    """Repository for managing entities."""
    
    @staticmethod
    async def get_all_entity_names(conn) -> list[str]:
        cursor = await conn.execute("SELECT name FROM entities")
        return [r[0] for r in await cursor.fetchall()]

    @staticmethod
    async def get_entity_details(conn, name: str) -> dict | None:
        cursor = await conn.execute("SELECT entity_type, description FROM entities WHERE name = ?", (name,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    async def upsert_entity(conn, name: str, entity_type: str, description: str, importance: int, agent_id: str):
        await conn.execute(
            "INSERT OR REPLACE INTO entities (name, entity_type, description, importance, updated_by) VALUES (?, ?, ?, ?, ?)",
            (name, entity_type, description, importance, agent_id),
        )

    @staticmethod
    async def increment_importance(conn, name: str):
        await conn.execute(
            "UPDATE entities SET importance = MIN(importance + 1, 10), updated_at = CURRENT_TIMESTAMP WHERE name = ?",
            (name,),
        )

    @staticmethod
    async def get_entities_by_names(conn, names: list[str]):
        if not names:
            return []
        placeholders = ",".join(["?"] * len(names))
        cursor = await conn.execute(
            f"SELECT * FROM entities WHERE name IN ({placeholders}) AND status = 'active'", names
        )
        return await cursor.fetchall()

class RelationRepository:
    """Repository for managing relations."""
    
    @staticmethod
    async def upsert_relation(conn, subject: str, object_name: str, predicate: str, agent_id: str):
        await conn.execute(
            "INSERT OR REPLACE INTO relations (subject, object, predicate, created_by) VALUES (?, ?, ?, ?)",
            (subject, object_name, predicate, agent_id),
        )

    @staticmethod
    async def upsert_relations_bulk(conn, relations: list[tuple[str, str, str, str]]):
        await conn.executemany(
            "INSERT OR REPLACE INTO relations (subject, object, predicate, created_by) VALUES (?, ?, ?, ?)",
            relations,
        )

    @staticmethod
    async def get_relations_by_subjects_or_objects(conn, names: list[str]):
        if not names:
            return []
        placeholders = ",".join(["?"] * len(names))
        cursor = await conn.execute(
            f"SELECT * FROM relations WHERE (subject IN ({placeholders}) OR object IN ({placeholders})) AND status = 'active'",
            names + names,
        )
        return await cursor.fetchall()

    @staticmethod
    async def get_relations_by_entity(conn, entity_name: str):
        cursor = await conn.execute(
            "SELECT * FROM relations WHERE (subject = ? OR object = ?) AND status='active'",
            (entity_name, entity_name),
        )
        return await cursor.fetchall()

class ObservationRepository:
    """Repository for managing observations."""
    
    @staticmethod
    async def get_recent_observations(conn, entity_name: str, limit: int = 5) -> list[str]:
        cursor = await conn.execute(
            "SELECT content FROM observations WHERE entity_name = ? ORDER BY timestamp DESC LIMIT ?",
            (entity_name, limit)
        )
        return [row[0] for row in await cursor.fetchall()]

    @staticmethod
    async def insert_observation(conn, entity_name: str, content: str, agent_id: str):
        await conn.execute(
            "INSERT INTO observations (entity_name, content, created_by) VALUES (?, ?, ?)",
            (entity_name, content, agent_id),
        )

    @staticmethod
    async def get_observations_by_entity_names(conn, names: list[str]):
        if not names:
            return []
        placeholders = ",".join(["?"] * len(names))
        cursor = await conn.execute(
            f"SELECT * FROM observations WHERE entity_name IN ({placeholders}) AND status = 'active'",
            names,
        )
        return await cursor.fetchall()

    @staticmethod
    async def get_active_observations_by_entity(conn, entity_name: str):
        cursor = await conn.execute(
            "SELECT content, timestamp FROM observations WHERE entity_name = ? AND status='active'",
            (entity_name,),
        )
        return await cursor.fetchall()

class ConflictRepository:
    """Repository for managing conflicts."""
    
    @staticmethod
    async def insert_conflict(conn, entity_name: str, existing_content: str, new_content: str, reason: str, agent_id: str):
        await conn.execute(
            "INSERT INTO conflicts (entity_name, existing_content, new_content, reason, agent_id) VALUES (?, ?, ?, ?, ?)",
            (entity_name, existing_content, new_content, reason, agent_id),
        )

class EmbeddingRepository:
    """Repository for managing embeddings."""
    
    @staticmethod
    async def upsert_embedding(conn, content_id: str, vector: list[float], model_name: str):
        await conn.execute(
            "INSERT OR REPLACE INTO embeddings (content_id, vector, model_name) VALUES (?, ?, ?)",
            (content_id, json.dumps(vector).encode("utf-8"), model_name),
        )

class TroubleshootingRepository:
    """Repository for managing troubleshooting knowledge."""
    
    @staticmethod
    async def insert_troubleshooting(conn, title: str, solution: str, affected_functions: str, env_metadata: str):
        await conn.execute(
            """
            INSERT INTO troubleshooting_knowledge (title, solution, affected_functions, env_metadata)
            VALUES (?, ?, ?, ?)
            """,
            (title, solution, affected_functions, env_metadata),
        )

    @staticmethod
    async def get_troubleshooting_by_ids(conn, ids: list[int]):
        if not ids:
            return []
        placeholders = ",".join(["?"] * len(ids))
        cursor = await conn.execute(
            f"SELECT * FROM troubleshooting_knowledge WHERE id IN ({placeholders})", ids
        )
        return await cursor.fetchall()

class TagRepository:
    """Repository for managing tags."""
    
    @staticmethod
    async def replace_tags(conn, content_id: str, content_type: str, tags: list[str]):
        await conn.execute(
            "DELETE FROM tags WHERE content_id = ? AND content_type = ?", (content_id, content_type)
        )
        data = [(t, content_id, content_type) for t in tags]
        await conn.executemany(
            "INSERT OR IGNORE INTO tags (tag, content_id, content_type) VALUES (?, ?, ?)", data
        )

    @staticmethod
    async def get_content_ids_by_tags(conn, tags: list[str]) -> list[str]:
        if not tags:
            return []
        placeholders = ",".join(["?"] * len(tags))
        cursor = await conn.execute(
            f"SELECT DISTINCT content_id FROM tags WHERE tag IN ({placeholders})", tags
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    @staticmethod
    async def search_tags(conn, query_words: list[str]):
        if not query_words:
            return []
        placeholders = ",".join(["?"] * len(query_words))
        cursor = await conn.execute(
            f"SELECT content_id, content_type, tag FROM tags WHERE tag IN ({placeholders})",
            [f"#{w}" for w in query_words],
        )
        return await cursor.fetchall()

class GraphRepository:
    """Repository for retrieving complete graph segments."""

    @staticmethod
    async def get_full_graph(conn):
        cursor = await conn.execute("SELECT * FROM entities WHERE status = 'active'")
        entities = await cursor.fetchall()
        cursor = await conn.execute("SELECT * FROM relations WHERE status = 'active'")
        relations = await cursor.fetchall()
        cursor = await conn.execute("SELECT * FROM observations WHERE status = 'active'")
        observations = await cursor.fetchall()
        return entities, relations, observations

    @staticmethod
    async def search_graph(conn, query: str):
        cursor = await conn.execute(
            "SELECT * FROM entities WHERE "
            "(name LIKE ? OR description LIKE ? OR entity_type LIKE ?) AND status = 'active'",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        matched_entities = await cursor.fetchall()
        entity_matched_names = [e["name"] for e in matched_entities]

        cursor = await conn.execute(
            "SELECT * FROM observations WHERE content LIKE ? AND status = 'active'",
            (f"%{query}%",),
        )
        direct_observations = await cursor.fetchall()
        obs_matched_entity_names = list(set([o["entity_name"] for o in direct_observations]))

        all_matched_names = list(set(entity_matched_names + obs_matched_entity_names))

        if not all_matched_names:
            return [], [], [], []

        placeholders = ",".join(["?"] * len(all_matched_names))
        cursor = await conn.execute(
            f"SELECT * FROM relations WHERE (subject IN ({placeholders}) "
            f"OR object IN ({placeholders})) AND status = 'active'",
            all_matched_names + all_matched_names,
        )
        relations = await cursor.fetchall()

        cursor = await conn.execute(
            "SELECT * FROM observations WHERE entity_name IN "
            f"({placeholders}) AND status = 'active'",
            all_matched_names,
        )
        linked_observations = await cursor.fetchall()
        
        return matched_entities, relations, direct_observations, linked_observations

class SearchRepository:
    """Repository for search operations."""

    @staticmethod
    async def perform_fts_search(conn, fts_table: str, id_col: str, content_col: str, title_col: str, fts_query: str):
        cursor = await conn.execute(
            f"SELECT {id_col}, {content_col}, {title_col}, bm25({fts_table}) "
            f"FROM {fts_table} WHERE {fts_table} MATCH ?",
            (fts_query,),
        )
        return await cursor.fetchall()

    @staticmethod
    async def perform_like_search(conn, table: str, id_col: str, content_col: str, query: str):
        cursor = await conn.execute(
            f"SELECT {id_col}, {content_col} FROM {table} "
            f"WHERE ({content_col} LIKE ? OR {id_col} LIKE ?) AND (status = 'active' OR 1=1)",
            (f"%{query}%", f"%{query}%"),
        )
        return await cursor.fetchall()

    @staticmethod
    async def get_all_embeddings(conn):
        cursor = await conn.execute("""
            SELECT e.content_id, e.vector
            FROM embeddings e
            LEFT JOIN entities ent ON e.content_id = ent.name
            LEFT JOIN bank_files bf ON e.content_id = bf.filename
            WHERE (ent.status = 'active' OR bf.status = 'active')
        """)
        return await cursor.fetchall()

class ThoughtRepository:
    """Repository for managing thought history."""

    @staticmethod
    async def init_tables(conn):
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS thought_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                thought_number INTEGER NOT NULL,
                total_thoughts INTEGER NOT NULL,
                thought TEXT NOT NULL,
                next_thought_needed BOOLEAN,
                is_revision BOOLEAN DEFAULT 0,
                revises_thought INTEGER,
                branch_from_thought INTEGER,
                branch_id TEXT,
                distilled BOOLEAN DEFAULT 0,
                meta_data TEXT,
                agent_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_thought_session ON thought_history (session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_thought_timestamp ON thought_history (timestamp)")
        await conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS thought_history_fts USING fts5(
                session_id, thought_number, thought, 
                content='thought_history', content_rowid='id'
            )
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS thought_history_ai AFTER INSERT ON thought_history BEGIN
                INSERT INTO thought_history_fts(rowid, session_id, thought_number, thought) 
                VALUES (new.id, new.session_id, new.thought_number, new.thought);
            END;
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS thought_history_ad AFTER DELETE ON thought_history BEGIN
                INSERT INTO thought_history_fts(thought_history_fts, rowid, 
                                                 session_id, thought_number, thought) 
                VALUES('delete', old.id, old.session_id, old.thought_number, old.thought);
            END;
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS thought_history_au AFTER UPDATE ON thought_history BEGIN
                INSERT INTO thought_history_fts(thought_history_fts, rowid, 
                                                 session_id, thought_number, thought) 
                VALUES('delete', old.id, old.session_id, old.thought_number, old.thought);
                INSERT INTO thought_history_fts(rowid, session_id, thought_number, thought) 
                VALUES (new.id, new.session_id, new.thought_number, new.thought);
            END;
        """)
        await conn.execute("INSERT INTO thought_history_fts(thought_history_fts) VALUES('rebuild')")

    @staticmethod
    async def apply_unique_index(conn):
        await conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_thought_number_unique "
            "ON thought_history (session_id, thought_number)"
        )

    @staticmethod
    async def apply_non_unique_index(conn):
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_thought_number "
            "ON thought_history (session_id, thought_number)"
        )

    @staticmethod
    async def check_thought_exists(conn, session_id: str, thought_number: int):
        cursor = await conn.execute(
            "SELECT id FROM thought_history "
            "WHERE session_id = ? AND thought_number = ?",
            (session_id, thought_number),
        )
        return await cursor.fetchone()

    @staticmethod
    async def insert_thought(conn, session_id, thought_number, total_thoughts, thought, next_thought_needed, is_revision, revises_thought, branch_from_thought, branch_id, agent_id, meta_data):
        await conn.execute(
            """
            INSERT INTO thought_history (
                session_id, thought_number, total_thoughts, thought,
                next_thought_needed, is_revision, revises_thought,
                branch_from_thought, branch_id, agent_id, meta_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id, thought_number, total_thoughts, thought,
                1 if next_thought_needed else 0, 1 if is_revision else 0,
                revises_thought, branch_from_thought, branch_id, agent_id, meta_data
            ),
        )

    @staticmethod
    async def get_session_stats(conn, session_id: str):
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM thought_history WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    @staticmethod
    async def update_thought_metadata(conn, session_id, thought_number, meta_data):
        await conn.execute(
            "UPDATE thought_history SET meta_data = ? "
            "WHERE session_id = ? AND thought_number = ?",
            (meta_data, session_id, thought_number),
        )

    @staticmethod
    async def mark_session_distilled(conn, session_id: str):
        await conn.execute(
            "UPDATE thought_history SET distilled = 1 WHERE session_id = ?",
            (session_id,),
        )

    @staticmethod
    async def get_session_history(conn, session_id: str):
        cursor = await conn.execute(
            "SELECT * FROM thought_history WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        return await cursor.fetchall()

    @staticmethod
    async def get_undistilled_sessions(conn):
        cursor = await conn.execute("""
            SELECT DISTINCT session_id FROM thought_history
            WHERE distilled = 0 AND next_thought_needed = 0
        """)
        return [row[0] for row in await cursor.fetchall()]

    @staticmethod
    async def get_stale_sessions(conn, minutes: int = 30):
        cursor = await conn.execute(f"""
            SELECT DISTINCT session_id FROM thought_history
            WHERE distilled = 0
            GROUP BY session_id
            HAVING MAX(timestamp) < datetime('now', '-{minutes} minutes')
        """)
        return [row[0] for row in await cursor.fetchall()]

    @staticmethod
    async def search_thoughts(conn, fts_query: str, exclude_session_id: str):
        cursor = await conn.execute(
            "SELECT session_id, thought_number, thought, bm25(thought_history_fts) "
            "FROM thought_history_fts WHERE thought_history_fts MATCH ? "
            "AND session_id != ?",
            (fts_query, exclude_session_id),
        )
        return await cursor.fetchall()

class MetadataRepository:
    """Repository for managing knowledge metadata."""

    @staticmethod
    async def get_all_metadata(conn):
        cursor = await conn.execute(
            "SELECT content_id, access_count, last_accessed FROM knowledge_metadata"
        )
        return await cursor.fetchall()
