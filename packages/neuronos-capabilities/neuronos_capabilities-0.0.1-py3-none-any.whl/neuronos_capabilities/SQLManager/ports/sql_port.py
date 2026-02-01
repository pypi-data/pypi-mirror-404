"""
Abstract port interface for SQL database operations.

This module defines the SQLPort abstract base class that all database adapters
must implement. It provides a provider-agnostic interface for all database operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import contextmanager, asynccontextmanager

# Type variable bound to SQLAlchemy DeclarativeBase
T = TypeVar('T')


class SQLPort(ABC):
    """
    Abstract interface for SQL database operations.

    All database adapters must implement this interface to provide provider-specific
    implementations while maintaining a consistent API. All operations support both
    synchronous and asynchronous execution.
    """

    # ===== Lifecycle Management =====

    @abstractmethod
    def connect(self) -> None:
        """
        Establish synchronous connection to the database.

        Creates connection pools and prepares the adapter for operations.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def connect_async(self) -> None:
        """
        Establish asynchronous connection to the database.

        Creates async connection pools and prepares the adapter for async operations.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close synchronous connection to the database.

        Closes all active connections and cleans up resources.
        """
        pass

    @abstractmethod
    async def disconnect_async(self) -> None:
        """
        Close asynchronous connection to the database.

        Closes all active async connections and cleans up resources.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the database connection is healthy (synchronous).

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def health_check_async(self) -> bool:
        """
        Check if the database connection is healthy (asynchronous).

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    # ===== Context Manager Support =====

    def __enter__(self):
        """Synchronous context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit."""
        self.disconnect()
        return False

    async def __aenter__(self):
        """Asynchronous context manager entry."""
        await self.connect_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        await self.disconnect_async()
        return False

    # ===== Schema & Migration Operations =====

    @abstractmethod
    def init_alembic(self, directory: str = "migrations") -> None:
        """
        Initialize Alembic for the project.

        Args:
            directory: Directory path for migrations

        Raises:
            MigrationError: If initialization fails
        """
        pass

    @abstractmethod
    def generate_migration(self, message: str, autogenerate: bool = True) -> str:
        """
        Generate a new migration file.

        Args:
            message: Migration message/description
            autogenerate: If True, auto-detect schema changes

        Returns:
            Revision ID of the generated migration

        Raises:
            MigrationError: If migration generation fails
        """
        pass

    @abstractmethod
    def apply_migrations(self, revision: str = "head") -> None:
        """
        Apply migrations up to specified revision (synchronous).

        Args:
            revision: Target revision ("head" for latest, "+1" for one step)

        Raises:
            MigrationError: If migration fails
        """
        pass

    @abstractmethod
    async def apply_migrations_async(self, revision: str = "head") -> None:
        """
        Apply migrations up to specified revision (asynchronous).

        Args:
            revision: Target revision ("head" for latest, "+1" for one step)

        Raises:
            MigrationError: If migration fails
        """
        pass

    @abstractmethod
    def downgrade_migration(self, revision: str = "-1") -> None:
        """
        Downgrade to a previous migration.

        Args:
            revision: Target revision ("-1" for one step back, "base" for initial)

        Raises:
            MigrationError: If downgrade fails
        """
        pass

    @abstractmethod
    def get_current_revision(self) -> Optional[str]:
        """
        Get current migration revision.

        Returns:
            Current revision ID or None if no migrations applied
        """
        pass

    @abstractmethod
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Get list of applied migrations.

        Returns:
            List of migration dictionaries with revision, message, etc.
        """
        pass

    # ===== Table Operations =====

    @abstractmethod
    def create_tables(self, models: Optional[List[Type[T]]] = None) -> None:
        """
        Create tables from SQLAlchemy models (synchronous).

        Args:
            models: List of model classes to create tables for.
                   If None, creates all registered models.

        Raises:
            TableError: If table creation fails
        """
        pass

    @abstractmethod
    async def create_tables_async(self, models: Optional[List[Type[T]]] = None) -> None:
        """
        Create tables from SQLAlchemy models (asynchronous).

        Args:
            models: List of model classes to create tables for.
                   If None, creates all registered models.

        Raises:
            TableError: If table creation fails
        """
        pass

    @abstractmethod
    def drop_tables(self, models: Optional[List[Type[T]]] = None) -> None:
        """
        Drop tables (synchronous).

        Args:
            models: List of model classes to drop tables for.
                   If None, drops all registered models.

        Raises:
            TableError: If table drop fails
        """
        pass

    @abstractmethod
    async def drop_tables_async(self, models: Optional[List[Type[T]]] = None) -> None:
        """
        Drop tables (asynchronous).

        Args:
            models: List of model classes to drop tables for.
                   If None, drops all registered models.

        Raises:
            TableError: If table drop fails
        """
        pass

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists (synchronous).

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        pass

    @abstractmethod
    async def table_exists_async(self, table_name: str) -> bool:
        """
        Check if table exists (asynchronous).

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        List all tables in database (synchronous).

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    async def list_tables_async(self) -> List[str]:
        """
        List all tables in database (asynchronous).

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    def list_schemas(self) -> List[str]:
        """
        List all schemas in database (synchronous) - PostgreSQL only.

        Returns:
            List of schema names

        Raises:
            TableError: If operation is not supported for the database provider
        """
        pass

    @abstractmethod
    async def list_schemas_async(self) -> List[str]:
        """
        List all schemas in database (asynchronous) - PostgreSQL only.

        Returns:
            List of schema names

        Raises:
            TableError: If operation is not supported for the database provider
        """
        pass

    @abstractmethod
    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """
        Get table schema information (synchronous).

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table schema information (columns, types, indexes, etc.)
        """
        pass

    @abstractmethod
    async def describe_table_async(self, table_name: str) -> Dict[str, Any]:
        """
        Get table schema information (asynchronous).

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table schema information (columns, types, indexes, etc.)
        """
        pass

    # ===== CRUD Operations - Create =====

    @abstractmethod
    def insert(self, model: Type[T], data: Dict[str, Any]) -> T:
        """
        Insert single record (synchronous).

        Args:
            model: SQLAlchemy model class
            data: Dictionary of column names and values

        Returns:
            Created model instance

        Raises:
            QueryError: If insert fails
        """
        pass

    @abstractmethod
    async def insert_async(self, model: Type[T], data: Dict[str, Any]) -> T:
        """
        Insert single record (asynchronous).

        Args:
            model: SQLAlchemy model class
            data: Dictionary of column names and values

        Returns:
            Created model instance

        Raises:
            QueryError: If insert fails
        """
        pass

    @abstractmethod
    def insert_many(self, model: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Bulk insert records (synchronous).

        Args:
            model: SQLAlchemy model class
            data_list: List of dictionaries with column names and values

        Returns:
            List of created model instances

        Raises:
            QueryError: If bulk insert fails
        """
        pass

    @abstractmethod
    async def insert_many_async(self, model: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Bulk insert records (asynchronous).

        Args:
            model: SQLAlchemy model class
            data_list: List of dictionaries with column names and values

        Returns:
            List of created model instances

        Raises:
            QueryError: If bulk insert fails
        """
        pass

    # ===== CRUD Operations - Read =====

    @abstractmethod
    def get_by_id(self, model: Type[T], id_value: Any) -> Optional[T]:
        """
        Get record by primary key (synchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_id_async(self, model: Type[T], id_value: Any) -> Optional[T]:
        """
        Get record by primary key (asynchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(
        self,
        model: Type[T],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all records with pagination (synchronous).

        Args:
            model: SQLAlchemy model class
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        pass

    @abstractmethod
    async def get_all_async(
        self,
        model: Type[T],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all records with pagination (asynchronous).

        Args:
            model: SQLAlchemy model class
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        pass

    @abstractmethod
    def query(
        self,
        model: Type[T],
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Query records with filters (synchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances matching the filters
        """
        pass

    @abstractmethod
    async def query_async(
        self,
        model: Type[T],
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Query records with filters (asynchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances matching the filters
        """
        pass

    @abstractmethod
    def count(self, model: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records (synchronous).

        Args:
            model: SQLAlchemy model class
            filters: Optional dictionary of filters

        Returns:
            Number of records matching the filters
        """
        pass

    @abstractmethod
    async def count_async(self, model: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records (asynchronous).

        Args:
            model: SQLAlchemy model class
            filters: Optional dictionary of filters

        Returns:
            Number of records matching the filters
        """
        pass

    # ===== CRUD Operations - Update =====

    @abstractmethod
    def update(self, model: Type[T], filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """
        Update records matching filters (synchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by
            updates: Dictionary of column names and new values

        Returns:
            Number of records updated

        Raises:
            QueryError: If update fails
        """
        pass

    @abstractmethod
    async def update_async(
        self,
        model: Type[T],
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """
        Update records matching filters (asynchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by
            updates: Dictionary of column names and new values

        Returns:
            Number of records updated

        Raises:
            QueryError: If update fails
        """
        pass

    @abstractmethod
    def update_by_id(self, model: Type[T], id_value: Any, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update single record by ID (synchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value
            updates: Dictionary of column names and new values

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            QueryError: If update fails
        """
        pass

    @abstractmethod
    async def update_by_id_async(
        self,
        model: Type[T],
        id_value: Any,
        updates: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update single record by ID (asynchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value
            updates: Dictionary of column names and new values

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            QueryError: If update fails
        """
        pass

    # ===== CRUD Operations - Delete =====

    @abstractmethod
    def delete(self, model: Type[T], filters: Dict[str, Any]) -> int:
        """
        Delete records matching filters (synchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by

        Returns:
            Number of records deleted

        Raises:
            QueryError: If delete fails
        """
        pass

    @abstractmethod
    async def delete_async(self, model: Type[T], filters: Dict[str, Any]) -> int:
        """
        Delete records matching filters (asynchronous).

        Args:
            model: SQLAlchemy model class
            filters: Dictionary of column names and values to filter by

        Returns:
            Number of records deleted

        Raises:
            QueryError: If delete fails
        """
        pass

    @abstractmethod
    def delete_by_id(self, model: Type[T], id_value: Any) -> bool:
        """
        Delete record by ID (synchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value

        Returns:
            True if record was deleted, False if not found

        Raises:
            QueryError: If delete fails
        """
        pass

    @abstractmethod
    async def delete_by_id_async(self, model: Type[T], id_value: Any) -> bool:
        """
        Delete record by ID (asynchronous).

        Args:
            model: SQLAlchemy model class
            id_value: Primary key value

        Returns:
            True if record was deleted, False if not found

        Raises:
            QueryError: If delete fails
        """
        pass

    @abstractmethod
    def truncate(self, model: Type[T]) -> None:
        """
        Truncate table (delete all records) (synchronous).

        Args:
            model: SQLAlchemy model class

        Raises:
            QueryError: If truncate fails
        """
        pass

    @abstractmethod
    async def truncate_async(self, model: Type[T]) -> None:
        """
        Truncate table (delete all records) (asynchronous).

        Args:
            model: SQLAlchemy model class

        Raises:
            QueryError: If truncate fails
        """
        pass

    # ===== Raw SQL Execution =====

    @abstractmethod
    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw SQL query (synchronous).

        Args:
            sql: SQL query string (use :param_name for parameters)
            params: Dictionary of parameter names and values

        Returns:
            Result of the execution

        Raises:
            QueryError: If execution fails
        """
        pass

    @abstractmethod
    async def execute_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw SQL query (asynchronous).

        Args:
            sql: SQL query string (use :param_name for parameters)
            params: Dictionary of parameter names and values

        Returns:
            Result of the execution

        Raises:
            QueryError: If execution fails
        """
        pass

    @abstractmethod
    def fetch_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch single result as dictionary (synchronous).

        Args:
            sql: SQL query string
            params: Dictionary of parameter names and values

        Returns:
            Single row as dictionary or None if no results

        Raises:
            QueryError: If query fails
        """
        pass

    @abstractmethod
    async def fetch_one_async(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single result as dictionary (asynchronous).

        Args:
            sql: SQL query string
            params: Dictionary of parameter names and values

        Returns:
            Single row as dictionary or None if no results

        Raises:
            QueryError: If query fails
        """
        pass

    @abstractmethod
    def fetch_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all results as dictionaries (synchronous).

        Args:
            sql: SQL query string
            params: Dictionary of parameter names and values

        Returns:
            List of rows as dictionaries

        Raises:
            QueryError: If query fails
        """
        pass

    @abstractmethod
    async def fetch_all_async(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all results as dictionaries (asynchronous).

        Args:
            sql: SQL query string
            params: Dictionary of parameter names and values

        Returns:
            List of rows as dictionaries

        Raises:
            QueryError: If query fails
        """
        pass

    # ===== Transaction Management =====

    @abstractmethod
    @contextmanager
    def begin_transaction(self):
        """
        Begin transaction (synchronous).

        Returns context manager for transaction.

        Example:
            with adapter.begin_transaction():
                adapter.insert(User, {"name": "Alice"})
                adapter.insert(User, {"name": "Bob"})
                # Auto-commits on exit, rolls back on exception

        Raises:
            TransactionError: If transaction fails
        """
        pass

    @abstractmethod
    @asynccontextmanager
    async def begin_transaction_async(self):
        """
        Begin transaction (asynchronous).

        Returns async context manager for transaction.

        Example:
            async with adapter.begin_transaction_async():
                await adapter.insert_async(User, {"name": "Alice"})
                await adapter.insert_async(User, {"name": "Bob"})
                # Auto-commits on exit, rolls back on exception

        Raises:
            TransactionError: If transaction fails
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """
        Commit current transaction (synchronous).

        Raises:
            TransactionError: If commit fails
        """
        pass

    @abstractmethod
    async def commit_async(self) -> None:
        """
        Commit current transaction (asynchronous).

        Raises:
            TransactionError: If commit fails
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback current transaction (synchronous).

        Raises:
            TransactionError: If rollback fails
        """
        pass

    @abstractmethod
    async def rollback_async(self) -> None:
        """
        Rollback current transaction (asynchronous).

        Raises:
            TransactionError: If rollback fails
        """
        pass
