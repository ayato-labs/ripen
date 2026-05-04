import asyncio
import json
from typing import Any

from shared_memory.common.utils import get_gemini_client, get_logger, log_error
from shared_memory.infra.database import async_get_connection, retry_on_db_lock

logger = get_logger(\"embeddings\")


async def compute_embeddings_bulk(texts: list[str]) -> list[list[float]]:
    \"\"\"
    Computes embeddings for a list of texts in parallel.
    Uses local cache to avoid redundant AI calls.
    \"\"\"
    if not texts:
        return []

    # 1. Check Cache
    tasks = [compute_embedding(text) for text in texts]
    vectors = await asyncio.gather(*tasks)
    return list(vectors)


async def compute_embedding(text: str) -> list[float]:
    \"\"\"Computes a single embedding with caching.\"\"\"
    if not text:
        return []

    # Try cache first
    cached = await _get_cached_embedding(text)
    if cached:
        return cached

    # Call Gemini
    client = get_gemini_client()
    if not client:
        return []

    try:
        # Gemini 2.0 embedding model
        # Using a lock to prevent concurrent API flooding if needed
        response = client.models.embed_content(
            model=\"text-embedding-004\",
            contents=text,
        )
        vector = response.embeddings[0].values

        # Save to cache in background
        asyncio.create_task(_save_to_cache(text, vector))
        return vector
    except Exception as e:
        log_error(f\"Embedding failed for text: {text[:50]}...\", e)
        return []


async def _get_cached_embedding(text: str) -> list[float] | None:
    \"\"\"Retrieves embedding from the database cache.\"\"\"
    try:
        from shared_memory.infra.database import async_get_connection

        async with async_get_connection() as db:
            cursor = await db.cursor()
            # Simple hash of text for key? No, aiosqlite handles strings fine
            await cursor.execute(\"SELECT embedding FROM embedding_cache WHERE text = ?\", (text,))
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
    except Exception:
        pass
    return None


async def _save_to_cache(text: str, vector: list[float]):
    \"\"\"Saves embedding to the database cache.\"\"\"
    try:
        from shared_memory.infra.database import async_get_connection

        async with async_get_connection() as db:
            cursor = await db.cursor()
            await cursor.execute(
                \"\"\"
                INSERT INTO embedding_cache (text, embedding)
                VALUES (?, ?)
                ON CONFLICT(text) DO NOTHING
                \"\"\",
                (text, json.dumps(vector)),
            )
            await db.commit()
    except Exception:
        pass
