import aiosqlite

from ripen.common.utils import get_logger

logger = get_logger("migration_v002")


async def migrate(conn: aiosqlite.Connection):
    """
    Migration v002: Change 'embedding_cache' PRIMARY KEY to composite key (content_hash, model_name).
    This allows cache entries for multiple models to coexist.
    """
    logger.info("Starting Migration v002...")

    await conn.execute("PRAGMA foreign_keys = OFF")

    try:
        logger.info("Reconstructing 'embedding_cache' table...")

        # Create new table with composite primary key
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache_new (
                content_hash TEXT,
                vector BLOB,
                model_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (content_hash, model_name)
            )
        """)

        # Check if model_name column exists in old table to prevent crash, fallback to default model if missing
        cursor = await conn.execute("PRAGMA table_info(embedding_cache)")
        columns = [row[1] for row in await cursor.fetchall()]

        if "model_name" in columns:
            # Copy data, substituting default fastembed model name if model_name is null
            await conn.execute("""
                INSERT OR IGNORE INTO embedding_cache_new (content_hash, vector, model_name, created_at)
                SELECT content_hash, vector, COALESCE(model_name, 'BAAI/bge-small-en-v1.5'), created_at
                FROM embedding_cache
            """)
        else:
            # If for some reason model_name didn't exist in the old table
            await conn.execute("""
                INSERT OR IGNORE INTO embedding_cache_new (content_hash, vector, model_name, created_at)
                SELECT content_hash, vector, 'BAAI/bge-small-en-v1.5', created_at
                FROM embedding_cache
            """)

        # Drop old, rename new
        await conn.execute("DROP TABLE IF EXISTS embedding_cache")
        await conn.execute("ALTER TABLE embedding_cache_new RENAME TO embedding_cache")

        logger.info("Migration v002 completed successfully.")

    except Exception as e:
        logger.error(f"Migration v002 failed: {e}")
        raise
    finally:
        await conn.execute("PRAGMA foreign_keys = ON")
