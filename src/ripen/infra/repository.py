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

class AuditRepository:
    """Repository for managing audit logs."""
    
    @staticmethod
    async def log_action(conn, table_name: str, content_id: str, action: str, old_data: str | None, new_data: str, agent_id: str):
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

class RelationRepository:
    """Repository for managing relations."""
    
    @staticmethod
    async def upsert_relation(conn, subject: str, object_name: str, predicate: str, agent_id: str):
        await conn.execute(
            "INSERT OR REPLACE INTO relations (subject, object, predicate, created_by) VALUES (?, ?, ?, ?)",
            (subject, object_name, predicate, agent_id),
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

class ObservationRepository:
    """Repository for managing observations."""
    
    @staticmethod
    async def get_recent_observations(conn, entity_name: str, limit: int = 5) -> list[str]:
        cursor = await conn.execute(
            "SELECT content FROM observations WHERE entity_name = ? ORDER BY timestamp DESC LIMIT ?",
            (entity_name, limit)
        )
        return [row[0] for row in await cursor.fetchall()]

class ConflictRepository:
    """Repository for managing conflicts."""
    
    @staticmethod
    async def insert_conflict(conn, entity_name: str, existing_content: str, new_content: str, reason: str, agent_id: str):
        await conn.execute(
            "INSERT INTO conflicts (entity_name, existing_content, new_content, reason, agent_id) VALUES (?, ?, ?, ?, ?)",
            (entity_name, existing_content, new_content, reason, agent_id),
        )
