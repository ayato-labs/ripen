from typing import Any

import pytest

from ripen.infra.repos_registry import repos_registry
from ripen.infra.repository_base import IEntityRepository
from ripen.infra.uow import UnitOfWork


# Mock entity repository implementation
class DummyEntityRepository(IEntityRepository):
    def __init__(self, conn):
        self.conn = conn

    async def get_all_entity_names(self) -> list[str]:
        return ["dummy-1", "dummy-2"]

    async def get_entity_details(self, name: str) -> dict | None:
        return {"name": name, "entity_type": "dummy", "description": "Mocked"}

    async def upsert_entity(self, name, entity_type, description, importance, agent_id) -> None:
        pass

    async def increment_importance(self, name: str) -> None:
        pass

    async def get_entities_by_names(self, names: list[str]) -> list[dict[str, Any]]:
        return []

    async def update_status(self, names, status) -> int:
        return 0

    async def get_inactive_entities(self) -> list[dict[str, Any]]:
        return []


@pytest.mark.asyncio
async def test_repos_registry_injection():
    # 1. Verify default setup (returns SQLite repository)
    from ripen.infra.repos import EntityRepository
    assert repos_registry.get_impl(IEntityRepository) == EntityRepository

    # 2. Register dummy implementation
    repos_registry.register(IEntityRepository, DummyEntityRepository)
    assert repos_registry.get_impl(IEntityRepository) == DummyEntityRepository

    # 3. Verify UnitOfWork binds the custom dummy repository
    async with UnitOfWork() as uow:
        assert isinstance(uow.entities, DummyEntityRepository)
        names = await uow.entities.get_all_entity_names()
        assert names == ["dummy-1", "dummy-2"]

    # 4. Reset to default to avoid affecting other tests
    repos_registry._reset_to_defaults()
    assert repos_registry.get_impl(IEntityRepository) == EntityRepository
