import asyncio
import json
import os

import aiosqlite

from shared_memory.common.utils import get_logger, get_thoughts_db_path, log_error
from shared_memory.infra.database import (
    _async_get_connection_raw,
    async_get_thoughts_connection,
    retry_on_db_lock,
)

logger = get_logger(\"thought_logic\")


async def init_thoughts_db(force: bool = False):
    \"\"\"Initializes the thoughts database if it doesn't exist.\"\"\"
    db_path = get_thoughts_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Use internal raw connection to avoid recursion during first-time init
    async with await _async_get_connection_raw(db_path, is_thoughts=True) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            \"\"\"
            CREATE TABLE IF NOT EXISTS thoughts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                thought_number INTEGER,
                total_thoughts INTEGER,
                thought TEXT,
                is_revision BOOLEAN,
                revises_thought INTEGER,
                branch_from_thought INTEGER,
                branch_id TEXT,
                next_thought_needed BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            \"\"\"
        )
        await cursor.execute(
            \"CREATE INDEX IF NOT EXISTS idx_thoughts_session ON thoughts(session_id)\"
        )
        await conn.commit()


@retry_on_db_lock()
async def save_thought(thought_data: dict):
    \"\"\"Saves a single thought to the database.\"\"\"
    await init_thoughts_db()

    async with async_get_thoughts_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            \"\"\"
            INSERT INTO thoughts (
                session_id, thought_number, total_thoughts, thought,
                is_revision, revises_thought, branch_from_thought,
                branch_id, next_thought_needed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\",
            (
                thought_data.get(\"session_id\"),
                thought_data.get(\"thought_number\"),
                thought_data.get(\"total_thoughts\"),
                thought_data.get(\"thought\"),
                thought_data.get(\"is_revision\"),
                thought_data.get(\"revises_thought\"),
                thought_data.get(\"branch_from_thought\"),
                thought_data.get(\"branch_id\"),
                thought_data.get(\"next_thought_needed\"),
            ),
        )
        await conn.commit()
        return \"Thought saved successfully\"


@retry_on_db_lock()
async def get_thoughts(session_id: str | None = None, limit: int = 100):
    \"\"\"Retrieves thoughts, optionally filtered by session.\"\"\"
    await init_thoughts_db()

    async with async_get_thoughts_connection() as conn:
        cursor = await conn.cursor()
        if session_id:
            await cursor.execute(
                \"SELECT * FROM thoughts WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?\",
                (session_id, limit),
            )
        else:
            await cursor.execute(\"SELECT * FROM thoughts ORDER BY timestamp DESC LIMIT ?\", (limit,))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
