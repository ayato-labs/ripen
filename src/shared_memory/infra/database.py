import os
import sqlite3
import json
from datetime import datetime
import aiosqlite
from shared_memory.common.exceptions import DatabaseError, DatabaseLockedError
from shared_memory.common.utils import get_db_path, get_logger, log_error
from shared_memory.infra.schema import TABLES, get_create_table_sql

logger = get_logger("database")

_DB_INITIALIZED = False
_SINGLETON_CONNECTION = None
_THOUGHTS_CONNECTION = None

@asynccontextmanager
async def async_get_connection():
    """
    Asynchronous connection context manager using a singleton pattern
    to avoid 'database is locked' errors in multi-agent environments.
    """
    global _SINGLETON_CONNECTION
    db_path = get_db_path()

    if _SINGLETON_CONNECTION is None or not _SINGLETON_CONNECTION.is_alive():
        _SINGLETON_CONNECTION = await _async_get_connection_raw(db_path)
        logger.info(f"Establishing NEW singleton connection to: {db_path}")

        # Configure PRAGMAs for performance and concurrency
        await _SINGLETON_CONNECTION.execute("PRAGMA journal_mode = WAL")
        await _SINGLETON_CONNECTION.execute("PRAGMA synchronous = NORMAL")
        await _SINGLETON_CONNECTION.execute("PRAGMA foreign_keys = ON")
        await _SINGLETON_CONNECTION.execute("PRAGMA busy_timeout = 5000")
        logger.info("Main connection successfully established and configured.")

    try:
        yield _SINGLETON_CONNECTION
        # No need to commit here; let the caller decide if needed.
    except Exception as e:
        logger.error(f"Error during async database operation: {e}")
        raise DatabaseError(f"Database operation failed: {e}")

@asynccontextmanager
async def async_get_thoughts_connection():
    """
    Returns a connection to the thoughts database.
    """
    global _THOUGHTS_CONNECTION
    db_path = os.path.join(os.path.dirname(get_db_path()), "thoughts.db")

    if _THOUGHTS_CONNECTION is None or not _THOUGHTS_CONNECTION.is_alive():
        _THOUGHTS_CONNECTION = await _async_get_connection_raw(db_path)
        logger.info(f"Establishing NEW thoughts singleton: {db_path}")
        await _THOUGHTS_CONNECTION.execute("PRAGMA journal_mode = WAL")
        await _THOUGHTS_CONNECTION.execute("PRAGMA synchronous = NORMAL")
        logger.info("Thoughts connection PRAGMAs configured (WAL/NORMAL).")

    try:
        yield _THOUGHTS_CONNECTION
    except Exception as e:
        logger.error(f"Error during thoughts database operation: {e}")
        raise DatabaseError(f"Thoughts database operation failed: {e}")

async def _async_get_connection_raw(db_path):
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn

def retry_on_db_lock(max_retries=5, initial_wait=0.2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for i in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (sqlite3.OperationalError, aiosqlite.OperationalError) as e:
                    if "database is locked" in str(e).lower():
                        last_error = e
                        wait_time = initial_wait * (2**i)
                        logger.warning(
                            f"Database locked. Retrying {i+1}/{max_retries} in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise
            logger.error(f"Failed after {max_retries} retries due to database lock: {last_error}")
            raise DatabaseLockedError(f"Database remains locked after retries: {last_error}")

        return wrapper

    return decorator

@retry_on_db_lock()
async def init_db(force: bool = False):
    global _DB_INITIALIZED
    if force:
        _DB_INITIALIZED = False
        await close_all_connections()

    if _DB_INITIALIZED:
        return

    logger.info(f"Initializing main database (force={force})...")

    # Ensure directory exists
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async with await _async_get_connection_raw(db_path) as conn:
        # Integrity Check: verify file is a database
        try:
            await conn.execute("SELECT 1")
            logger.info("DB Integrity Check: PASSED.")
        except (aiosqlite.DatabaseError, sqlite3.DatabaseError) as e:
            logger.error(f"DB Integrity Check: FAILED. {e}")
            raise

        logger.info("Starting table creation/verification sequence...")
        cursor = await conn.cursor()
        try:
            # SSoT: Initialize all tables defined in schema.py
            for table_name in TABLES:
                sql = get_create_table_sql(table_name)
                await cursor.execute(sql)
            
            # Create Indices defined in schema.py
            for table in TABLES.values():
                if table.indices:
                    for idx in table.indices:
                        idx_cols = ", ".join(idx.columns)
                        unique = "UNIQUE" if idx.is_unique else ""
                        await cursor.execute(
                            f"CREATE {unique} INDEX IF NOT EXISTS {idx.name} ON {table.name}({idx_cols})"
                        )

            logger.info(f"Core tables ({', '.join(TABLES.keys())}) verified via SSoT.")
        except Exception:
            logger.exception("CRITICAL: Failed to create/verify core tables")
            raise

        # --- Full Text Search (FTS5) Support ---
        await cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
                name,
                description,
                content='entities',
                tokenize='unicode61 remove_diacritics 1'
            )
        """)
        await cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
                entity_name,
                content,
                content='observations',
                tokenize='unicode61 remove_diacritics 1'
            )
        """)
        await cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS bank_files_fts USING fts5(
                filename,
                content,
                content='bank_files',
                tokenize='unicode61 remove_diacritics 1'
            )
        """)

        # Triggers for FTS synchronization
        # Entities
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS entities_ai AFTER INSERT ON entities BEGIN
              INSERT INTO entities_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS entities_ad AFTER DELETE ON entities BEGIN
              INSERT INTO entities_fts(entities_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS entities_au AFTER UPDATE ON entities BEGIN
              INSERT INTO entities_fts(entities_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
              INSERT INTO entities_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
            END;
        """)

        # Observations
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
              INSERT INTO observations_fts(rowid, entity_name, content) VALUES (new.rowid, new.entity_name, new.content);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
              INSERT INTO observations_fts(observations_fts, rowid, entity_name, content) VALUES('delete', old.rowid, old.entity_name, old.content);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_au AFTER UPDATE ON observations BEGIN
              INSERT INTO observations_fts(observations_fts, rowid, entity_name, content) VALUES('delete', old.rowid, old.entity_name, old.content);
              INSERT INTO observations_fts(rowid, entity_name, content) VALUES (new.rowid, new.entity_name, new.content);
            END;
        """)

        # Bank Files
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bank_files_ai AFTER INSERT ON bank_files BEGIN
              INSERT INTO bank_files_fts(rowid, filename, content) VALUES (new.rowid, new.filename, new.content);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bank_files_ad AFTER DELETE ON bank_files BEGIN
              INSERT INTO bank_files_fts(bank_files_fts, rowid, filename, content) VALUES('delete', old.rowid, old.filename, old.content);
            END;
        """)
        await cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bank_files_au AFTER UPDATE ON bank_files BEGIN
              INSERT INTO bank_files_fts(bank_files_fts, rowid, filename, content) VALUES('delete', old.rowid, old.filename, old.content);
              INSERT INTO bank_files_fts(rowid, filename, content) VALUES (new.rowid, new.filename, new.content);
            END;
        """)

        # Run Migrations
        from shared_memory.migrations.manager import MigrationManager
        migrator = MigrationManager(db_path)
        await migrator.run_migrations(conn)

        await conn.commit()
        logger.info("Main database initialization successful.")

    _DB_INITIALIZED = True

async def close_all_connections():
    """Explicitly closes all singleton connections (useful for tests)."""
    global _SINGLETON_CONNECTION, _THOUGHTS_CONNECTION, _DB_INITIALIZED
    logger.info("Closing all singleton database connections...")
    if _SINGLETON_CONNECTION:
        await _SINGLETON_CONNECTION.close()
        _SINGLETON_CONNECTION = None
    if _THOUGHTS_CONNECTION:
        await _THOUGHTS_CONNECTION.close()
        _THOUGHTS_CONNECTION = None
    _DB_INITIALIZED = False

async def _add_column_if_missing(cursor, table_name, column_def):
    """
    Helper to add columns to existing tables during migration.
    Deprecated: Use MigrationManager for future changes.
    """
    column_name = column_def.split()[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in await cursor.fetchall()]
    if column_name not in columns:
        logger.info(f"Adding missing column '{column_name}' to table '{table_name}'...")
        await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
