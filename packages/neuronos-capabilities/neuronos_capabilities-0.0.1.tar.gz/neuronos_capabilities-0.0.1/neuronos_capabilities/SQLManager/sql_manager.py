"""
SQLManager - Public API for SQL database operations.

This is the main entrypoint that users import and use for all database operations.
Implements singleton pattern to prevent connection saturation.
"""

from typing import Any, Dict, List, Optional, Type, Union
from contextlib import contextmanager, asynccontextmanager

from .config.sql_config import SQLConfig
from .ports.sql_port import SQLPort
from .adapters.postgres_adapter import PostgresAdapter
from .utils.singleton import SingletonRegistry
from .exceptions.sql_exceptions import SQLManagerError, ConfigurationError


class SQLManager:
    """
    Public API for SQL database operations with singleton pattern.

    This class provides a clean, consistent interface for all database operations
    while managing connection pools efficiently through a singleton registry.

    Example:
        # Basic usage
        config = {
            "host": "localhost",
            "database": "myapp",
            "user": "postgres",
            "password": "secret"
        }

        with SQLManager(config) as db:
            user = db.insert(User, {"name": "Alice"})
            users = db.query(User, {"name": "Alice"})

        # Async usage
        async with SQLManager(config) as db:
            user = await db.insert_async(User, {"name": "Bob"})
    """

    _registry = SingletonRegistry()

    def __init__(self, config: Optional[Union[SQLConfig, Dict[str, Any]]] = None):
        """
        Initialize SQLManager with configuration.

        Args:
            config: SQLConfig object or dictionary with connection parameters

        Raises:
            ConfigurationError: If configuration is invalid or missing
        """
        if config is None:
            raise ConfigurationError("Configuration is required")

        # Convert dict to SQLConfig if needed
        if isinstance(config, dict):
            try:
                config = SQLConfig(**config)
            except Exception as e:
                raise ConfigurationError(f"Invalid configuration: {str(e)}")

        self.config = config
        self._adapter: Optional[SQLPort] = None

        # Generate unique key for singleton registry
        config_key = self._generate_config_key(config)

        # Check if instance already exists in registry
        existing_adapter = self._registry.get(config_key)
        if existing_adapter:
            self._adapter = existing_adapter
            self._is_singleton_reuse = True
        else:
            # Create new adapter and register it
            self._adapter = self._create_adapter(config)
            self._registry.register(config_key, self._adapter)
            self._is_singleton_reuse = False

    def _generate_config_key(self, config: SQLConfig) -> str:
        """
        Generate unique key from config for singleton registry.

        Args:
            config: SQLConfig object

        Returns:
            Unique string identifier for this configuration
        """
        return f"{config.provider}://{config.host}:{config.port}/{config.database}_{config.user}"

    def _create_adapter(self, config: SQLConfig) -> SQLPort:
        """
        Factory method to create appropriate adapter based on provider.

        Args:
            config: SQLConfig object

        Returns:
            Adapter instance implementing SQLPort

        Raises:
            ConfigurationError: If provider is not supported
        """
        provider = config.provider.lower()

        if provider == "postgresql":
            return PostgresAdapter(config)
        else:
            raise ConfigurationError(
                f"Unsupported provider: {config.provider}. "
                f"Currently supported: postgresql"
            )

    # ===== Connection Management =====

    def connect(self) -> "SQLManager":
        """
        Establish database connection (synchronous).

        Returns:
            Self for method chaining

        Raises:
            ConnectionError: If connection fails
        """
        # Always connect, even for singleton reuse, in case it was previously disconnected
        if self._adapter.sync_engine is None:
            self._adapter.connect()
        return self

    async def connect_async(self) -> "SQLManager":
        """
        Establish database connection (asynchronous).

        Returns:
            Self for method chaining

        Raises:
            ConnectionError: If connection fails
        """
        # Always connect, even for singleton reuse, in case it was previously disconnected
        if self._adapter.async_engine is None:
            await self._adapter.connect_async()
        return self

    def disconnect(self) -> None:
        """Close database connection (synchronous)."""
        if self._adapter:
            self._adapter.disconnect()

    async def disconnect_async(self) -> None:
        """Close database connection (asynchronous)."""
        if self._adapter:
            await self._adapter.disconnect_async()

    def health_check(self) -> bool:
        """
        Check if database connection is healthy (synchronous).

        Returns:
            True if connection is healthy, False otherwise
        """
        return self._adapter.health_check()

    async def health_check_async(self) -> bool:
        """
        Check if database connection is healthy (asynchronous).

        Returns:
            True if connection is healthy, False otherwise
        """
        return await self._adapter.health_check_async()

    # ===== Context Manager Support =====

    def __enter__(self) -> "SQLManager":
        """Synchronous context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Synchronous context manager exit."""
        self.disconnect()

    async def __aenter__(self) -> "SQLManager":
        """Asynchronous context manager entry."""
        await self.connect_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Asynchronous context manager exit."""
        await self.disconnect_async()

    # ===== Schema & Migration Operations =====

    def init_alembic(self, directory: str = "migrations") -> None:
        """Initialize Alembic for the project."""
        return self._adapter.init_alembic(directory)

    def generate_migration(self, message: str, autogenerate: bool = True) -> str:
        """Generate a new migration file."""
        return self._adapter.generate_migration(message, autogenerate)

    def apply_migrations(self, revision: str = "head") -> None:
        """Apply migrations (sync)."""
        return self._adapter.apply_migrations(revision)

    async def apply_migrations_async(self, revision: str = "head") -> None:
        """Apply migrations (async)."""
        return await self._adapter.apply_migrations_async(revision)

    def downgrade_migration(self, revision: str = "-1") -> None:
        """Downgrade to a previous migration."""
        return self._adapter.downgrade_migration(revision)

    def get_current_revision(self) -> Optional[str]:
        """Get current migration revision."""
        return self._adapter.get_current_revision()

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations."""
        return self._adapter.get_migration_history()

    def stamp_migration(self, revision: str = "head") -> None:
        """
        Stamp database with a migration revision without running migrations.

        This is useful when tables already exist and you want to mark them as migrated.

        Args:
            revision: Revision to stamp (default: "head" for latest)
        """
        return self._adapter.stamp_migration(revision)

    def check_migration_sync(self) -> Dict[str, Any]:
        """
        Check if database schema is in sync with migration files.

        Returns:
            Dictionary with sync status information including:
            - current_revision: Current migration revision
            - head_revision: Latest migration revision
            - in_sync: Boolean indicating if database is up to date
            - pending_migrations: List of pending migrations
            - existing_tables: List of tables in database
            - has_tables: Boolean indicating if tables exist
        """
        return self._adapter.check_migration_sync()

    def remove_duplicate_migrations(self) -> int:
        """
        Detect and remove duplicate migration files.

        This is useful when you accidentally generate the same migration twice,
        which can cause "table already exists" errors.

        Returns:
            Number of duplicate files removed

        Example:
            with SQLManager(config) as db:
                removed = db.remove_duplicate_migrations()
                print(f"Removed {removed} duplicate migrations")
        """
        return self._adapter.remove_duplicate_migrations()

    def apply_migrations_smart(self, revision: str = "head", auto_stamp_on_conflict: bool = True) -> None:
        """
        Intelligently apply migrations with automatic handling of edge cases.

        This method will:
        - Automatically detect and remove duplicate migration files
        - Automatically stamp database if tables exist but no migrations recorded
        - Auto-stamp on duplicate table errors to resolve conflicts (if auto_stamp_on_conflict=True)
        - Provide helpful error messages and suggestions

        Args:
            revision: Target revision (default: "head" for latest)
            auto_stamp_on_conflict: If True, automatically stamp database when duplicate
                                   table errors occur. This resolves conflicts by marking
                                   migrations as applied without executing them. (default: True)

        Example:
            # Auto-resolve conflicts (recommended for development)
            db.apply_migrations_smart()

            # Fail on conflicts (recommended for production)
            db.apply_migrations_smart(auto_stamp_on_conflict=False)
        """
        return self._adapter.apply_migrations_smart(revision, auto_stamp_on_conflict)

    # ===== Table Operations =====

    def create_tables(self, models: Optional[List[Type]] = None) -> None:
        """Create tables from SQLAlchemy models (sync)."""
        return self._adapter.create_tables(models)

    async def create_tables_async(self, models: Optional[List[Type]] = None) -> None:
        """Create tables from SQLAlchemy models (async)."""
        return await self._adapter.create_tables_async(models)

    def drop_tables(self, models: Optional[List[Type]] = None) -> None:
        """Drop tables (sync)."""
        return self._adapter.drop_tables(models)

    async def drop_tables_async(self, models: Optional[List[Type]] = None) -> None:
        """Drop tables (async)."""
        return await self._adapter.drop_tables_async(models)

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists (sync)."""
        return self._adapter.table_exists(table_name)

    async def table_exists_async(self, table_name: str) -> bool:
        """Check if table exists (async)."""
        return await self._adapter.table_exists_async(table_name)

    def list_tables(self) -> List[str]:
        """List all tables in database (sync)."""
        return self._adapter.list_tables()

    async def list_tables_async(self) -> List[str]:
        """List all tables in database (async)."""
        return await self._adapter.list_tables_async()

    def list_schemas(self) -> List[str]:
        """List all schemas in database (sync) - PostgreSQL only."""
        return self._adapter.list_schemas()

    async def list_schemas_async(self) -> List[str]:
        """List all schemas in database (async) - PostgreSQL only."""
        return await self._adapter.list_schemas_async()

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information (sync)."""
        return self._adapter.describe_table(table_name)

    async def describe_table_async(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information (async)."""
        return await self._adapter.describe_table_async(table_name)

    # ===== CRUD Operations - Create =====

    def insert(self, model: Type, data: Dict[str, Any]):
        """Insert single record (sync)."""
        return self._adapter.insert(model, data)

    async def insert_async(self, model: Type, data: Dict[str, Any]):
        """Insert single record (async)."""
        return await self._adapter.insert_async(model, data)

    def insert_many(self, model: Type, data_list: List[Dict[str, Any]]) -> List:
        """Bulk insert records (sync)."""
        return self._adapter.insert_many(model, data_list)

    async def insert_many_async(self, model: Type, data_list: List[Dict[str, Any]]) -> List:
        """Bulk insert records (async)."""
        return await self._adapter.insert_many_async(model, data_list)

    # ===== CRUD Operations - Read =====

    def get_by_id(self, model: Type, id_value: Any) -> Optional:
        """Get record by primary key (sync)."""
        return self._adapter.get_by_id(model, id_value)

    async def get_by_id_async(self, model: Type, id_value: Any) -> Optional:
        """Get record by primary key (async)."""
        return await self._adapter.get_by_id_async(model, id_value)

    def get_all(self, model: Type, limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Get all records with pagination (sync)."""
        return self._adapter.get_all(model, limit, offset)

    async def get_all_async(self, model: Type, limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Get all records with pagination (async)."""
        return await self._adapter.get_all_async(model, limit, offset)

    def query(self, model: Type, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Query records with filters (sync)."""
        return self._adapter.query(model, filters, limit, offset)

    async def query_async(self, model: Type, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Query records with filters (async)."""
        return await self._adapter.query_async(model, filters, limit, offset)

    def count(self, model: Type, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records (sync)."""
        return self._adapter.count(model, filters)

    async def count_async(self, model: Type, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records (async)."""
        return await self._adapter.count_async(model, filters)

    # ===== CRUD Operations - Update =====

    def update(self, model: Type, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records matching filters (sync)."""
        return self._adapter.update(model, filters, updates)

    async def update_async(self, model: Type, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records matching filters (async)."""
        return await self._adapter.update_async(model, filters, updates)

    def update_by_id(self, model: Type, id_value: Any, updates: Dict[str, Any]) -> Optional:
        """Update single record by ID (sync)."""
        return self._adapter.update_by_id(model, id_value, updates)

    async def update_by_id_async(self, model: Type, id_value: Any, updates: Dict[str, Any]) -> Optional:
        """Update single record by ID (async)."""
        return await self._adapter.update_by_id_async(model, id_value, updates)

    # ===== CRUD Operations - Delete =====

    def delete(self, model: Type, filters: Dict[str, Any]) -> int:
        """Delete records matching filters (sync)."""
        return self._adapter.delete(model, filters)

    async def delete_async(self, model: Type, filters: Dict[str, Any]) -> int:
        """Delete records matching filters (async)."""
        return await self._adapter.delete_async(model, filters)

    def delete_by_id(self, model: Type, id_value: Any) -> bool:
        """Delete record by ID (sync)."""
        return self._adapter.delete_by_id(model, id_value)

    async def delete_by_id_async(self, model: Type, id_value: Any) -> bool:
        """Delete record by ID (async)."""
        return await self._adapter.delete_by_id_async(model, id_value)

    def truncate(self, model: Type) -> None:
        """Truncate table (sync)."""
        return self._adapter.truncate(model)

    async def truncate_async(self, model: Type) -> None:
        """Truncate table (async)."""
        return await self._adapter.truncate_async(model)

    # ===== Raw SQL Execution =====

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query (sync)."""
        return self._adapter.execute(sql, params)

    async def execute_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query (async)."""
        return await self._adapter.execute_async(sql, params)

    def fetch_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result as dictionary (sync)."""
        return self._adapter.fetch_one(sql, params)

    async def fetch_one_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result as dictionary (async)."""
        return await self._adapter.fetch_one_async(sql, params)

    def fetch_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results as dictionaries (sync)."""
        return self._adapter.fetch_all(sql, params)

    async def fetch_all_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results as dictionaries (async)."""
        return await self._adapter.fetch_all_async(sql, params)

    # ===== Transaction Management =====

    @contextmanager
    def begin_transaction(self):
        """Begin transaction (sync). Returns context manager."""
        with self._adapter.begin_transaction() as session:
            yield session

    @asynccontextmanager
    async def begin_transaction_async(self):
        """Begin transaction (async). Returns async context manager."""
        async with self._adapter.begin_transaction_async() as session:
            yield session

    def commit(self) -> None:
        """Commit current transaction (sync)."""
        return self._adapter.commit()

    async def commit_async(self) -> None:
        """Commit current transaction (async)."""
        return await self._adapter.commit_async()

    def rollback(self) -> None:
        """Rollback current transaction (sync)."""
        return self._adapter.rollback()

    async def rollback_async(self) -> None:
        """Rollback current transaction (async)."""
        return await self._adapter.rollback_async()
