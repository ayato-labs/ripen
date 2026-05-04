import json
import os
import time
from typing import Any

import aiosqlite

from shared_memory.common.utils import get_logger, log_error
from shared_memory.core import search
from shared_memory.infra.database import (
    async_get_connection,
    get_write_semaphore,
    retry_on_db_lock,
)
from shared_memory.infra.embeddings import compute_embeddings_bulk

logger = get_logger("bank")


async def read_bank_data() -> dict[str, Any]:
    \"\"\"Retrieves all data from the knowledge_bank table.\"\"\"
    try:
        async with async_get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(\"\"\"
                SELECT filename, content, last_updated, importance
                FROM knowledge_bank
            \"\"\" )
            rows = await cursor.fetchall()
            return {row["filename"]: dict(row) for row in rows}
    except Exception as e:
        log_error("Failed to read bank data", e)
        return {}


@retry_on_db_lock()
async def save_bank_files(
    bank_files: dict[str, str],
    agent_id: str,
    conn: aiosqlite.Connection,
    precomputed_vectors: list[list[float]] | None = None,
) -> str:
    \"\"\"Saves multiple files to the knowledge bank using the provided connection.\"\"\"
    results = []
    vector_idx = 0
    for filename, content in bank_files.items():
        try:
            # 1. Update/Insert into knowledge_bank
            await conn.execute(
                \"\"\"
                INSERT INTO knowledge_bank (filename, content, agent_id, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(filename) DO UPDATE SET
                    content = excluded.content,
                    agent_id = excluded.agent_id,
                    last_updated = CURRENT_TIMESTAMP
            \"\"\",
                (filename, content, agent_id),
            )

            # 2. Update metadata (Importance, etc.)
            content_id = f"bank:{filename}"
            from shared_memory.infra.database import update_access

            await update_access(content_id, conn=conn)

            # 3. Handle Vector Persistence
            if precomputed_vectors and vector_idx < len(precomputed_vectors):
                vector = precomputed_vectors[vector_idx]
                vector_idx += 1
            else:
                logger.info(f"Computing embedding for bank file: {filename}")
                vector = await compute_embeddings_bulk([f"File: {filename}\nContent: {content}"])
                vector = vector[0]

            await conn.execute(
                \"\"\"
                INSERT INTO embedding_cache (content_hash, vector, model_name)
                VALUES (?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET vector = excluded.vector
            \"\"\",
                (
                    f"bank:{filename}",
                    json.dumps(vector),
                    "gemini-text-embedding-004",
                ),
            )

            results.append(f"Saved {filename}")
        except Exception as e:
            logger.exception(f"Failed to save bank file: {filename}")
            results.append(f"Error saving {filename}: {e}")

    return ", ".join(results)


async def repair_memory_logic():
    \"\"\"
    Core logic for checking and repairing memory consistency.
    Currently: ensures all bank files have corresponding metadata and embeddings.
    \"\"\"
    logger.info("Starting memory repair process...")
    try:
        async with async_get_connection() as conn:
            # 1. Find bank files without metadata
            cursor = await conn.execute(\"\"\"
                SELECT filename FROM knowledge_bank
                WHERE NOT EXISTS (
                    SELECT 1 FROM knowledge_metadata 
                    WHERE content_id = 'bank:' || filename
                )
            \"\"\")
            orphans = [row[0] for row in await cursor.fetchall()]

            if orphans:
                logger.info(f"Found {len(orphans)} orphans. Repairing...")
                from shared_memory.infra.database import update_access

                for filename in orphans:
                    await update_access(f"bank:{filename}", conn=conn)
                await conn.commit()

            # 2. Find bank files without embeddings
            cursor = await conn.execute(\"\"\"
                SELECT filename, content FROM knowledge_bank
                WHERE NOT EXISTS (
                    SELECT 1 FROM embedding_cache 
                    WHERE content_hash = 'bank:' || filename
                )
            \"\"\")
            missing_embeds = await cursor.fetchall()

            if missing_embeds:
                logger.info(f"Re-computing {len(missing_embeds)} missing embeddings...")
                for row in missing_embeds:
                    filename, content = row
                    vector = await compute_embeddings_bulk(
                        [f"File: {filename}\nContent: {content}"]
                    )
                    await conn.execute(
                        \"\"\"
                        INSERT OR REPLACE INTO embedding_cache (content_hash, vector, model_name)
                        VALUES (?, ?, ?)
                    \"\"\",
                        (
                            f"bank:{filename}",
                            json.dumps(vector[0]),
                            "gemini-text-embedding-004",
                        ),
                    )
                await conn.commit()

            return f"Repair complete. Fixed {len(orphans)} metadata, {len(missing_embeds)} embeddings."
    except Exception as e:
        log_error("Memory repair failed", e)
        return f"Repair failed: {e}"


@retry_on_db_lock()
async def delete_bank_file(filename: str) -> str:
    \"\"\"Deletes a file from the knowledge bank.\"\"\"
    try:
        async with async_get_connection() as conn:
            await conn.execute(\"\"\"
                DELETE FROM knowledge_bank WHERE filename = ?
            \"\"\", (filename,))
            await conn.execute(\"\"\"
                DELETE FROM knowledge_metadata WHERE content_id = ?
            \"\"\", (f"bank:{filename}",))
            await conn.execute(\"\"\"
                DELETE FROM embedding_cache WHERE content_hash = ?
            \"\"\", (f"bank:{filename}",))
            await conn.commit()
            return f"Deleted {filename} from bank."
    except Exception as e:
        log_error(f"Failed to delete bank file {filename}", e)
        return f"Error deleting {filename}: {e}"
