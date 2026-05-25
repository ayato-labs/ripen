import json
from ripen.common.config import settings
from ripen.common.utils import get_logger
from ripen.infra.embeddings import compute_embedding

logger = get_logger("migration_ops")


async def migrate_embeddings_if_needed(uow) -> None:
    """
    Checks if stored embeddings match the current configured embedding model.
    If there are mismatches, automatically recalculates and updates them.
    """
    target_model = settings.embedding_model
    if not target_model:
        logger.warning("No embedding model configured. Skipping automatic recalculation check.")
        return

    # 1. Fetch mismatching entries
    cursor = await uow.execute(
        "SELECT content_id, model_name FROM embeddings WHERE model_name IS NULL OR model_name != ?",
        (target_model,),
    )
    mismatches = await cursor.fetchall()
    if not mismatches:
        logger.debug("All embeddings are up-to-date with current model.")
        return

    logger.info(
        f"Detected {len(mismatches)} embeddings using outdated models. "
        f"Migrating to '{target_model}'..."
    )

    # Separate into entities and bank files to resolve original texts
    content_ids = [row[0] for row in mismatches]
    
    # 2. Retrieve original text data
    # 2.1 For Entities
    entity_map = {}
    if content_ids:
        # Generate placeholders for IN clause
        placeholders = ",".join("?" for _ in content_ids)
        entities_cursor = await uow.execute(
            f"SELECT name, entity_type, description FROM entities WHERE name IN ({placeholders})",
            content_ids,
        )
        for name, e_type, desc in await entities_cursor.fetchall():
            entity_map[name] = f"{name} ({e_type or 'concept'}): {desc or ''}"

    # 2.2 For Bank Files
    bank_map = {}
    if content_ids:
        placeholders = ",".join("?" for _ in content_ids)
        bank_cursor = await uow.execute(
            f"SELECT filename, content FROM bank_files WHERE filename IN ({placeholders})",
            content_ids,
        )
        for filename, content in await bank_cursor.fetchall():
            bank_map[filename] = f"File: {filename}\nContent: {content or ''}"

    # 3. Batch compute new embeddings
    to_calculate = []
    ids_to_calculate = []
    
    for cid in content_ids:
        if cid in entity_map:
            to_calculate.append(entity_map[cid])
            ids_to_calculate.append(cid)
        elif cid in bank_map:
            to_calculate.append(bank_map[cid])
            ids_to_calculate.append(cid)
        else:
            logger.warning(f"Could not find source text for content_id: {cid}. Skipping.")

    if not to_calculate:
        logger.info("No source text found for any mismatched embeddings.")
        return

    logger.info(f"Recalculating embeddings for {len(to_calculate)} items...")
    
    # Compute using the existing compute_embedding (which handles caching and rate-limiting)
    # Using batch size of 20 to avoid exceeding API payload limits or rate limits
    batch_size = 20
    new_vectors = []
    
    for i in range(0, len(to_calculate), batch_size):
        batch_texts = to_calculate[i : i + batch_size]
        logger.debug(f"Recalculating batch {i // batch_size + 1} ({len(batch_texts)} items)...")
        try:
            batch_vectors = await compute_embedding(batch_texts)
            # compute_embedding returns single vector if list size is 1, but we pass list so it returns list of vectors
            if isinstance(batch_vectors, list):
                new_vectors.extend(batch_vectors)
            else:
                new_vectors.append(batch_vectors)
        except Exception as e:
            logger.error(f"Failed to compute embeddings for batch {i // batch_size + 1}: {e}")
            logger.error("Embedding migration aborted. Some embeddings remain outdated.")
            return

    # 4. Save newly calculated embeddings back to database
    updated_count = 0
    for cid, vector in zip(ids_to_calculate, new_vectors, strict=True):
        try:
            await uow.embeddings.upsert_embedding(cid, vector, target_model)
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to save migrated embedding for '{cid}': {e}")

    logger.info(f"Successfully migrated {updated_count}/{len(to_calculate)} embeddings to '{target_model}'.")
