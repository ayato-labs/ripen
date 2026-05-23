from typing import Any

import aiosqlite

from ripen.infra.database import AsyncSQLiteConnection, get_write_semaphore, init_db
from ripen.infra.repos_registry import repos_registry
from ripen.infra.repository_base import IManagementRepository


class UnitOfWork:
    """
    Manages database transactions and ensures repository instances
    share the same connection within a session.
    """

    def __init__(self, is_thoughts: bool = False):
        self.is_thoughts = is_thoughts
        self._conn: aiosqlite.Connection | None = None
        self._semaphore = get_write_semaphore(is_thoughts)
        self._management: IManagementRepository | None = None

    async def __aenter__(self):
        from ripen.common.utils import get_logger
        log = get_logger("uow")
        log.debug(f"UOW_START: is_thoughts={self.is_thoughts}")
        
        if repos_registry.connection_factory:
            self._conn = await repos_registry.connection_factory(self.is_thoughts)
        elif self.is_thoughts:
            from ripen.common.utils import get_thoughts_db_path
            from ripen.core.thought_logic import init_thoughts_db

            await init_thoughts_db()
            self._conn = await AsyncSQLiteConnection(
                get_thoughts_db_path(), is_thoughts=True
            ).__aenter__()
        else:
            from ripen.common.utils import get_db_path

            await init_db()
            self._conn = await AsyncSQLiteConnection(get_db_path()).__aenter__()

        log.debug("UOW_READY: Connection acquired and repositories bound")
        # Initialize repositories with this connection using repos_registry
        self.bank = repos_registry.create_bank_repository(self._conn)
        self.audit = repos_registry.create_audit_repository(self._conn)
        self.entities = repos_registry.create_entity_repository(self._conn)
        self.relations = repos_registry.create_relation_repository(self._conn)
        self.observations = repos_registry.create_observation_repository(self._conn)
        self.conflicts = repos_registry.create_conflict_repository(self._conn)
        self.embeddings = repos_registry.create_embedding_repository(self._conn)
        self.troubleshooting = repos_registry.create_troubleshooting_repository(self._conn)
        self.tags = repos_registry.create_tag_repository(self._conn)
        self.graph = repos_registry.create_graph_repository(self._conn)
        self.search = repos_registry.create_search_repository(self._conn)
        self.thoughts = repos_registry.create_thought_repository(self._conn)
        self.metadata = repos_registry.create_metadata_repository(self._conn)
        self._management = repos_registry.create_management_repository(self._conn)

        return self

    @property
    def management(self) -> IManagementRepository:
        return self._management

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        from ripen.common.utils import get_logger
        log = get_logger("uow")
        if exc_type:
            log.warning(f"UOW_EXIT: Exception detected ({exc_type.__name__}). Rolling back.")
            await self.rollback()
        else:
            log.debug("UOW_EXIT: Normal exit. Committing.")
            await self.commit()
        # The connection itself is a singleton managed by database.py
        # and doesn't need to be closed here, but we should clear our reference.
        self._conn = None

    async def commit(self):
        if self._conn:
            await self._conn.commit()

    async def rollback(self):
        if self._conn:
            await self._conn.rollback()

    async def execute(self, sql: str, params: Any = None):
        return await self._conn.execute(sql, params)


class SecureWriteContext:
    """
    Context manager that combines the write semaphore and a UnitOfWork.
    """

    def __init__(self, is_thoughts: bool = False):
        self.is_thoughts = is_thoughts
        self.uow = UnitOfWork(is_thoughts)
        self._semaphore = get_write_semaphore(is_thoughts)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return await self.uow.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.uow.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._semaphore.release()
