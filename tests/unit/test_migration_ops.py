import json
from unittest.mock import PropertyMock, patch

import pytest

from ripen.common.config import settings
from ripen.infra.database import init_db
from ripen.infra.uow import SecureWriteContext, UnitOfWork
from ripen.ops.migration_ops import migrate_embeddings_if_needed


@pytest.mark.asyncio
async def test_migrate_embeddings_if_needed_no_mismatch():
    """Verify that migration_ops does nothing if model names match."""
    await init_db(force=True)

    # Use current settings default fastembed model name
    current_model = settings.embedding_model

    async with SecureWriteContext() as uow:
        # Prepopulate one entity and its embedding with the correct current model name
        await uow.entities.upsert_entity("Entity1", "concept", "Desc1", 5, "default_agent")
        dummy_vector = [0.1, 0.2, 0.3]
        await uow.embeddings.upsert_embedding("Entity1", dummy_vector, current_model)
        await uow.commit()

    # Run the migration check
    with patch("ripen.ops.migration_ops.compute_embedding") as mock_compute:
        async with UnitOfWork() as uow:
            await migrate_embeddings_if_needed(uow)
        
        # Should not call compute_embedding because there is no mismatch
        mock_compute.assert_not_called()


@pytest.mark.asyncio
async def test_migrate_embeddings_if_needed_with_mismatch():
    """Verify that migration_ops automatically updates mismatched embeddings."""
    await init_db(force=True)

    old_model = "old-model-name"
    new_model = "new-model-name"

    # Setup temporary mock settings so settings.embedding_model returns the new model
    patch_target = "ripen.common.config.Settings.embedding_model"
    with patch(patch_target, new_callable=PropertyMock) as mock_embed_model:
        mock_embed_model.return_value = new_model
        assert settings.embedding_model == new_model

        # 1. Insert database records with OLD model name
        async with SecureWriteContext() as uow:
            await uow.entities.upsert_entity("EntityM", "concept", "DescM", 5, "default_agent")
            await uow.bank.upsert_bank_file("fileM.md", "ContentM", "default_agent")
            
            # Mock embedding for old model (2-dimensional vector)
            await uow.embeddings.upsert_embedding("EntityM", [0.1, 0.1], old_model)
            await uow.embeddings.upsert_embedding("fileM.md", [0.2, 0.2], old_model)
            await uow.commit()

        # 2. Run recalculation with new model
        async def mock_compute_impl(text_list):
            # Returns 3-dimensional dummy vector for new model
            if isinstance(text_list, str):
                return [0.9, 0.9, 0.9]
            return [[0.9, 0.9, 0.9]] * len(text_list)

        patch_compute = "ripen.ops.migration_ops.compute_embedding"
        with patch(patch_compute, side_effect=mock_compute_impl) as mock_compute:
            async with SecureWriteContext() as uow:
                await migrate_embeddings_if_needed(uow)
                await uow.commit()

            # Verify that compute_embedding was called
            mock_compute.assert_called_once()

        # 3. Assert database results are updated to new model and new vector dimensions
        async with UnitOfWork() as uow:
            cursor = await uow.execute("SELECT content_id, vector, model_name FROM embeddings")
            rows = await cursor.fetchall()
            assert len(rows) == 2
            for row in rows:
                assert row["model_name"] == new_model
                vector_data = json.loads(row["vector"])
                assert len(vector_data) == 3
                assert vector_data == [0.9, 0.9, 0.9]


@pytest.mark.asyncio
async def test_cache_coexistence_with_composite_pk():
    """Verify that multiple model cache entries coexist in the database due to composite PK."""
    # Ensure table creation and schema migration v002 is run
    await init_db(force=True)

    content_hash = "dummyhash12345"
    vector_model1 = [0.1, 0.1]
    vector_model2 = [0.2, 0.2, 0.2]
    model1 = "model1"
    model2 = "model2"

    async with SecureWriteContext() as uow:
        # Insert cache entry for model1
        await uow.embeddings.insert_cache_entry(content_hash, vector_model1, model1)
        # Insert cache entry for model2 for the SAME content_hash
        await uow.embeddings.insert_cache_entry(content_hash, vector_model2, model2)
        await uow.commit()

    # Assert both coexist (no overwrite occurred)
    async with UnitOfWork() as uow:
        cached1 = await uow.embeddings.get_cached_embedding(content_hash, model1)
        cached2 = await uow.embeddings.get_cached_embedding(content_hash, model2)
        
        assert cached1 == vector_model1
        assert cached2 == vector_model2
        
        # Verify directly in SQLite that count is 2 for this hash
        cursor = await uow.execute(
            "SELECT COUNT(*) FROM embedding_cache WHERE content_hash = ?", (content_hash,)
        )
        count = (await cursor.fetchone())[0]
        assert count == 2
