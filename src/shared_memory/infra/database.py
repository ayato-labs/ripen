import asyncio
import json
import os
import random
import sqlite3
from contextlib import asynccontextmanager

import aiosqlite

from shared_memory.common.exceptions import DatabaseError, DatabaseLockedError
from shared_memory.common.utils import get_db_path, get_logger, log_error
from shared_memory.infra.schema import (
    FTS_TABLES,
    FTS_TRIGGERS,
    TABLES,
    get_create_table_sql,
)

logger = get_logger("database")

# Global singletons for persistent connections
_MAIN_CONNECTION: aiosqlite.Connection | None = None
_THOUGHTS_CONNECTION: aiosqlite.Connection | None = None

# Global lock to prevent race conditions during singleton initialization
_INIT_LOCK: asyncio.Lock | None = None


def _get_init_lock() -> asyncio.Lock:
    global _INIT_LOCK
    if _INIT_LOCK is None:
        _INIT_LOCK = asyncio.Lock()
    return _INIT_LOCK


# Global flag to track if the main database has been initialized in the current session.
_DB_INITIALIZED = False


def retry_on_db_lock(max_retries=15, initial_delay=0.1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except (aiosqlite.OperationalError, DatabaseError, sqlite3.OperationalError) as e:
                    error_str = str(e).lower()
                    if "database is locked" in error_str:
                        retries += 1
                        delay = min(initial_delay * (2 ** (retries - 1)), 1.0) + random.uniform(
                            0, 0.1
                        )
                        logger.warning(
                            f"DATABASE LOCKED: Attempt {retries}/{max_retries}. "
                            f"Waiting {delay:.2f}s before retry. "
                            f"(Source: {func.__name__}, Error: {e})"
                        )
                        if retries == max_retries:
                            logger.error(
                                f"DATABASE FATAL: Max retries ({max_retries}) "
                                f"exceeded for {func.__name__}. Giving up."
                            )
                            raise DatabaseLockedError(
                                f"Database remained locked after {max_retries} attempts."
                            ) from e
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"DATABASE ERROR: Non-lock error in {func.__name__}: {e}")
                        raise e
            return await func(*args, **kwargs)

        return wrapper

    return decorator


@asynccontextmanager
async def async_get_connection():
    \"\"\"
    Singleton connection provider for the main database.
    Usage: async with async_get_connection() as conn:
    \"\"\"
    global _MAIN_CONNECTION
    await init_db()

    async with _get_init_lock():
        if _MAIN_CONNECTION is None:
            db_path = get_db_path()
            try:
                _MAIN_CONNECTION = await aiosqlite.connect(db_path, timeout=30.0)
                _MAIN_CONNECTION.row_factory = aiosqlite.Row
                await _MAIN_CONNECTION.execute("PRAGMA foreign_keys = ON")
                await _MAIN_CONNECTION.execute("PRAGMA journal_mode = WAL")
                await _MAIN_CONNECTION.execute("PRAGMA synchronous = NORMAL")
                logger.info(f"Established main DB singleton: {db_path}")
            except Exception as e:
                raise DatabaseError(f"Failed to connect to main DB: {e}") from e

    try:
        yield _MAIN_CONNECTION
    except Exception as e:
        logger.error(f"Error during main DB operation: {e}")
        raise DatabaseError(f"Main DB operation failed: {e}") from e


@asynccontextmanager
async def async_get_thoughts_connection():
    \"\"\"
    Singleton connection provider for the thoughts database.
    Usage: async with async_get_thoughts_connection() as conn:
    \"\"\"
    global _THOUGHTS_CONNECTION
    from shared_memory.common.utils import get_thoughts_db_path
    from shared_memory.core.thought_logic import init_thoughts_db

    await init_thoughts_db()

    async with _get_init_lock():
        if _THOUGHTS_CONNECTION is None:
            db_path = get_thoughts_db_path()
            try:
                _THOUGHTS_CONNECTION = await aiosqlite.connect(db_path, timeout=30.0)
                _THOUGHTS_CONNECTION.row_factory = aiosqlite.Row
                await _THOUGHTS_CONNECTION.execute("PRAGMA journal_mode = WAL")
                await _THOUGHTS_CONNECTION.execute("PRAGMA synchronous = NORMAL")
                logger.info(f"Established thoughts DB singleton: {db_path}")
            except Exception as e:
                raise DatabaseError(f"Failed to connect to thoughts DB: {e}") from e

    try:
        yield _THOUGHTS_CONNECTION
    except Exception as e:
        logger.error(f"Error during thoughts DB operation: {e}")
        raise DatabaseError(f"Thoughts DB operation failed: {e}") from e


async def close_all_connections():
    \"\"\"Closes all singleton connections.\"\"\"
    global _MAIN_CONNECTION, _THOUGHTS_CONNECTION, _DB_INITIALIZED
    async with _get_init_lock():
        if _MAIN_CONNECTION:
            await _MAIN_CONNECTION.close()
            _MAIN_CONNECTION = None
        if _THOUGHTS_CONNECTION:
            await _THOUGHTS_CONNECTION.close()
            _THOUGHTS_CONNECTION = None
        _DB_INITIALIZED = False
    logger.info("Closed all DB connections.")


@retry_on_db_lock()
async def init_db(force: bool = False):
    global _DB_INITIALIZED
    if force:
        await close_all_connections()

    if _DB_INITIALIZED:
        return

    async with _get_init_lock():
        if _DB_INITIALIZED:
            return

        db_path = get_db_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.cursor()

            # 1. Create Tables (SSoT)
            for table_name in TABLES:
                await cursor.execute(get_create_table_sql(table_name))

            # 2. Create Indices (SSoT)
            for table in TABLES.values():
                if table.indices:
                    for idx in table.indices:
                        cols = ", ".join(idx.columns)
                        unique = "UNIQUE" if idx.is_unique else ""
                        await cursor.execute(
                            f"CREATE {unique} INDEX IF NOT EXISTS {idx.name} ON {table.name}({cols})"
                        )

            # 3. Create FTS Tables (SSoT)
            for fts_name, fts_def in FTS_TABLES.items():
                await cursor.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts_name} {fts_def}")

            # 4. Create Triggers (SSoT)
            for trigger_sql in FTS_TRIGGERS:
                await cursor.execute(trigger_sql)

            # 5. FTS Rebuild
            for fts_name in FTS_TABLES:
                await cursor.execute(f"INSERT INTO {fts_name}({fts_name}) VALUES('rebuild')")

            await conn.commit()

            # 6. Run Migrations
            from shared_memory.migrations.manager import MigrationManager

            migrator = MigrationManager(db_path)
            await migrator.run_migrations(conn)

            _DB_INITIALIZED = True
            logger.info("Database initialized successfully via SSoT.")


@retry_on_db_lock()
async def update_access(content_id: str, conn=None):
    # Guard: Ensure DB is initialized before any access update
    await init_db()
    if conn is None:
        async with async_get_connection() as managed_conn:
            await managed_conn.execute(
                \"\"\"
                INSERT INTO knowledge_metadata (
                    content_id, access_count, last_accessed,
                    importance_score, stability, decay_rate
                )
                VALUES (?, 1, CURRENT_TIMESTAMP, 1.0, 1.1, 0.01)
                ON CONFLICT(content_id) DO UPDATE SET
                    access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP,
                    stability = stability * 1.1
                \"\"\",
                (content_id,),
            )
            await managed_conn.commit()
    else:
        await conn.execute(
            \"\"\"
            INSERT INTO knowledge_metadata (
                content_id, access_count, last_accessed,
                importance_score, stability, decay_rate
            )
            VALUES (?, 1, CURRENT_TIMESTAMP, 1.0, 1.1, 0.01)
            ON CONFLICT(content_id) DO UPDATE SET
                access_count = access_count + 1,
                last_accessed = CURRENT_TIMESTAMP,
                stability = stability * 1.1
        \"\"\",
            (content_id,),
        )


@retry_on_db_lock()
async def log_search_stat(
    query: str,
    results_count: int,
    hit_ids: list[str] = None,
    avg_sim: float = 0.0,
    conn=None,
):
    \"\"\"
    Logs the result count of a search for hit rate and knowledge age calculation.
    \"\"\"
    # Guard: Ensure DB is initialized before logging stats
    await init_db()

    hit_ids_json = json.dumps(hit_ids or [])

    async def _execute(c):
        await c.execute(
            \"\"\"
            INSERT INTO search_stats (
                query, results_count, hit_content_ids, avg_similarity
            ) VALUES (?, ?, ?, ?)
            \"\"\",
            (query, results_count, hit_ids_json, avg_sim),
        )
        await c.commit()

    if conn is not None:
        await _execute(conn)
    else:
        async with async_get_connection() as managed_conn:
            await _execute(managed_conn)
