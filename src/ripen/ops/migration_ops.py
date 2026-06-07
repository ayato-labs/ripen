from ripen.common.config import settings
from ripen.common.utils import get_logger
from ripen.infra.embeddings import compute_embedding

logger = get_logger("migration_ops")


async def _get_mismatched_embeddings(uow, target_model: str) -> list[str]:
    """Retrieves all content IDs where the embedding model does not match target_model."""
    cursor = await uow.execute(
        "SELECT content_id FROM embeddings WHERE model_name IS NULL OR model_name != ?",
        (target_model,),
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def _resolve_original_texts(
    uow, content_ids: list[str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Resolves the original text content for the given entities and bank files."""
    entity_map = {}
    bank_map = {}
    if not content_ids:
        return entity_map, bank_map

    placeholders = ",".join("?" for _ in content_ids)

    # 1. Fetch Entities
    entities_cursor = await uow.execute(
        f"SELECT name, entity_type, description FROM entities WHERE name IN ({placeholders})",
        content_ids,
    )
    for name, e_type, desc in await entities_cursor.fetchall():
        entity_map[name] = f"{name} ({e_type or 'concept'}): {desc or ''}"

    # 2. Fetch Bank Files
    bank_cursor = await uow.execute(
        f"SELECT filename, content FROM bank_files WHERE filename IN ({placeholders})",
        content_ids,
    )
    for filename, content in await bank_cursor.fetchall():
        bank_map[filename] = f"File: {filename}\nContent: {content or ''}"

    return entity_map, bank_map


def _build_calculation_inputs(
    content_ids: list[str], entity_map: dict[str, str], bank_map: dict[str, str]
) -> tuple[list[str], list[str]]:
    """Filters and pairs content IDs with their resolved text representation."""
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

    return to_calculate, ids_to_calculate


async def _compute_batch_vectors(
    to_calculate: list[str], batch_size: int = 20
) -> list[list[float]] | None:
    """Computes embeddings for the input texts in batches."""
    new_vectors = []
    for i in range(0, len(to_calculate), batch_size):
        batch_texts = to_calculate[i : i + batch_size]
        logger.debug(f"Recalculating batch {i // batch_size + 1} ({len(batch_texts)} items)...")
        try:
            batch_vectors = await compute_embedding(batch_texts)
            if isinstance(batch_vectors, list):
                new_vectors.extend(batch_vectors)
            else:
                new_vectors.append(batch_vectors)
        except Exception as e:
            logger.error(f"Failed to compute embeddings for batch {i // batch_size + 1}: {e}")
            logger.error("Embedding migration aborted. Some embeddings remain outdated.")
            return None
    return new_vectors


async def _save_migrated_embeddings(
    uow, ids_to_calculate: list[str], new_vectors: list[list[float]], target_model: str
) -> int:
    """Saves the recalculated vectors back into the embeddings table."""
    updated_count = 0
    for cid, vector in zip(ids_to_calculate, new_vectors, strict=True):
        try:
            await uow.embeddings.upsert_embedding(cid, vector, target_model)
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to save migrated embedding for '{cid}': {e}")
    return updated_count


async def migrate_embeddings_if_needed(uow) -> None:
    """
    Checks if stored embeddings match the current configured embedding model.
    If there are mismatches, automatically recalculates and updates them.
    """
    target_model = settings.embedding_model
    if not target_model:
        logger.warning("No embedding model configured. Skipping automatic recalculation check.")
        return

    content_ids = await _get_mismatched_embeddings(uow, target_model)
    if not content_ids:
        logger.debug("All embeddings are up-to-date with current model.")
        return

    logger.info(
        f"Detected {len(content_ids)} embeddings using outdated models. "
        f"Migrating to '{target_model}'..."
    )

    entity_map, bank_map = await _resolve_original_texts(uow, content_ids)
    to_calculate, ids_to_calculate = _build_calculation_inputs(content_ids, entity_map, bank_map)

    if not to_calculate:
        logger.info("No source text found for any mismatched embeddings.")
        return

    logger.info(f"Recalculating embeddings for {len(to_calculate)} items...")
    new_vectors = await _compute_batch_vectors(to_calculate)
    if new_vectors is None:
        return

    updated_count = await _save_migrated_embeddings(
        uow, ids_to_calculate, new_vectors, target_model
    )
    logger.info(
        f"Successfully migrated {updated_count}/{len(to_calculate)} "
        f"embeddings to '{target_model}'."
    )
