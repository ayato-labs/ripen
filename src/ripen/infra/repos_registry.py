from collections.abc import Callable
from typing import Any

# Interface classes
from ripen.infra.repository_base import (
    IAuditRepository,
    IBankRepository,
    IConflictRepository,
    IEmbeddingRepository,
    IEntityRepository,
    IGraphRepository,
    IManagementRepository,
    IMetadataRepository,
    IObservationRepository,
    IRelationRepository,
    ISearchRepository,
    ITagRepository,
    IThoughtRepository,
    ITroubleshootingRepository,
)


class RepositoryRegistry:
    def __init__(self):
        self._registry = {}
        self._connection_factory = None
        self._db_init_hook = None
        self._db_close_hook = None
        self._reset_to_defaults()

    def _reset_to_defaults(self):
        from ripen.infra import repos

        self._registry[IEntityRepository] = repos.EntityRepository
        self._registry[IBankRepository] = repos.BankRepository
        self._registry[IAuditRepository] = repos.AuditRepository
        self._registry[IRelationRepository] = repos.RelationRepository
        self._registry[IObservationRepository] = repos.ObservationRepository
        self._registry[IConflictRepository] = repos.ConflictRepository
        self._registry[IEmbeddingRepository] = repos.EmbeddingRepository
        self._registry[ITroubleshootingRepository] = repos.TroubleshootingRepository
        self._registry[ITagRepository] = repos.TagRepository
        self._registry[IGraphRepository] = repos.GraphRepository
        self._registry[ISearchRepository] = repos.SearchRepository
        self._registry[IThoughtRepository] = repos.ThoughtRepository
        self._registry[IMetadataRepository] = repos.MetadataRepository
        self._registry[IManagementRepository] = repos.ManagementRepository

    def register(self, interface_class: type, impl_class: type):
        """Allows registering a custom repository implementation (e.g. for Postgres)."""
        self._registry[interface_class] = impl_class

    def get_impl(self, interface_class: type) -> type:
        return self._registry[interface_class]

    # Helper builders to be used in UoW
    def create_entity_repository(self, conn: Any) -> IEntityRepository:
        return self._registry[IEntityRepository](conn)

    def create_bank_repository(self, conn: Any) -> IBankRepository:
        return self._registry[IBankRepository](conn)

    def create_audit_repository(self, conn: Any) -> IAuditRepository:
        return self._registry[IAuditRepository](conn)

    def create_relation_repository(self, conn: Any) -> IRelationRepository:
        return self._registry[IRelationRepository](conn)

    def create_observation_repository(self, conn: Any) -> IObservationRepository:
        return self._registry[IObservationRepository](conn)

    def create_conflict_repository(self, conn: Any) -> IConflictRepository:
        return self._registry[IConflictRepository](conn)

    def create_embedding_repository(self, conn: Any) -> IEmbeddingRepository:
        return self._registry[IEmbeddingRepository](conn)

    def create_troubleshooting_repository(self, conn: Any) -> ITroubleshootingRepository:
        return self._registry[ITroubleshootingRepository](conn)

    def create_tag_repository(self, conn: Any) -> ITagRepository:
        return self._registry[ITagRepository](conn)

    def create_graph_repository(self, conn: Any) -> IGraphRepository:
        return self._registry[IGraphRepository](conn)

    def create_search_repository(self, conn: Any) -> ISearchRepository:
        return self._registry[ISearchRepository](conn)

    def create_thought_repository(self, conn: Any) -> IThoughtRepository:
        return self._registry[IThoughtRepository](conn)

    def create_metadata_repository(self, conn: Any) -> IMetadataRepository:
        return self._registry[IMetadataRepository](conn)

    def create_management_repository(self, conn: Any) -> IManagementRepository:
        return self._registry[IManagementRepository](conn)

    # Hooks for database connection & setup overriding
    def register_connection_factory(self, factory: Callable[[bool], Any]):
        """Override connection logic (e.g. return PostgreSQL pool/connection)."""
        self._connection_factory = factory

    def register_db_init_hook(self, hook: Callable[[bool], Any]):
        """Override standard DB schema initialization."""
        self._db_init_hook = hook

    def register_db_close_hook(self, hook: Callable[[], Any]):
        """Override database closing logic."""
        self._db_close_hook = hook

    @property
    def connection_factory(self) -> Callable[[bool], Any] | None:
        return self._connection_factory

    @property
    def db_init_hook(self) -> Callable[[bool], Any] | None:
        return self._db_init_hook

    @property
    def db_close_hook(self) -> Callable[[], Any] | None:
        return self._db_close_hook


repos_registry = RepositoryRegistry()
