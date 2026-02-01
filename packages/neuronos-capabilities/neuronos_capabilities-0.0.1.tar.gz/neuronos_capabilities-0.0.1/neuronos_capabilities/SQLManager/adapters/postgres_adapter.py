"""
PostgreSQL adapter implementation of SQLPort interface.

This module provides the concrete implementation of all database operations
for PostgreSQL using SQLAlchemy Core + ORM with both sync and async support.
"""

from typing import Any, Dict, List, Optional, Type
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import (
    create_engine, select, update, delete, func, inspect, text
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)
from sqlalchemy.pool import NullPool

from ..ports.sql_port import SQLPort
from ..config.sql_config import SQLConfig
from ..exceptions.sql_exceptions import (
    ConnectionError as SQLConnectionError,
    QueryError,
    MigrationError,
    TransactionError,
    TableError,
    ModelError,
)
from ..migrations.alembic_manager import AlembicManager
from ..utils.query_builder import (
    build_filter_clause,
    get_primary_key_column,
    get_primary_key_name,
    get_table_name,
)


class PostgresAdapter(SQLPort):
    """
    PostgreSQL implementation of the SQLPort interface.

    This adapter uses SQLAlchemy with psycopg2 (sync) and asyncpg (async)
    drivers to provide full database functionality for PostgreSQL.

    Attributes:
        config: SQLConfig object with connection settings
        sync_engine: Synchronous SQLAlchemy engine
        async_engine: Asynchronous SQLAlchemy engine
        session_factory: Factory for creating sync sessions
        async_session_factory: Factory for creating async sessions
        alembic_manager: AlembicManager for migrations
    """

    def __init__(self, config: SQLConfig):
        """
        Initialize PostgreSQL adapter.

        Args:
            config: SQLConfig object with connection parameters
        """
        self.config = config
        self.sync_engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self.alembic_manager = None
        self._current_session = None
        self._current_async_session = None

    # ===== Lifecycle Management =====

    def connect(self) -> None:
        """Establish synchronous database connection."""
        try:
            connection_string = self.config.get_connection_string(async_mode=False)

            self.sync_engine = create_engine(
                connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=self.config.echo_sql,
            )

            self.session_factory = sessionmaker(
                bind=self.sync_engine,
                autocommit=self.config.autocommit,
                autoflush=True,
            )

            # Set schema in the Base model if configured
            if self.config.schema:
                from ..models.base import set_schema
                set_schema(self.config.schema)

            # Initialize Alembic manager with schema support
            self.alembic_manager = AlembicManager(
                connection_string=connection_string,
                migrations_dir=self.config.migrations_directory,
                metadata=None,  # Will use Base.metadata from models.base
                schema=self.config.schema,
            )

            # Test connection and create schema if needed
            with self.sync_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

                # Create schema if it doesn't exist (PostgreSQL only)
                if self.config.schema and self.config.provider == "postgresql":
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}"))
                    conn.commit()

        except Exception as e:
            raise SQLConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")

    async def connect_async(self) -> None:
        """Establish asynchronous database connection."""
        try:
            connection_string = self.config.get_connection_string(async_mode=True)

            self.async_engine = create_async_engine(
                connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=self.config.echo_sql,
            )

            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                autocommit=self.config.autocommit,
                autoflush=True,
                class_=AsyncSession,
            )

            # Set schema in the Base model if configured
            if self.config.schema:
                from ..models.base import set_schema
                set_schema(self.config.schema)

            # Test connection and create schema if needed
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

                # Create schema if it doesn't exist (PostgreSQL only)
                if self.config.schema and self.config.provider == "postgresql":
                    await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}"))
                    await conn.commit()

        except Exception as e:
            raise SQLConnectionError(f"Failed to connect to PostgreSQL async: {str(e)}")

    def disconnect(self) -> None:
        """Close synchronous database connection."""
        if self.sync_engine:
            self.sync_engine.dispose()
            self.sync_engine = None
            self.session_factory = None

    async def disconnect_async(self) -> None:
        """Close asynchronous database connection."""
        if self.async_engine:
            await self.async_engine.dispose()
            self.async_engine = None
            self.async_session_factory = None

    def health_check(self) -> bool:
        """Check if database connection is healthy (sync)."""
        try:
            with self.sync_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def health_check_async(self) -> bool:
        """Check if database connection is healthy (async)."""
        try:
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    # ===== Schema & Migration Operations =====

    def init_alembic(self, directory: str = "migrations") -> None:
        """Initialize Alembic for the project."""
        try:
            self.config.migrations_directory = directory
            if self.alembic_manager:
                self.alembic_manager.migrations_dir = directory
                self.alembic_manager.config = self.alembic_manager._create_config()
                self.alembic_manager.init()
            else:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
        except Exception as e:
            raise MigrationError(f"Failed to initialize Alembic: {str(e)}")

    def generate_migration(self, message: str, autogenerate: bool = True) -> str:
        """Generate a new migration file."""
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            return self.alembic_manager.create_migration(message, autogenerate)
        except Exception as e:
            raise MigrationError(f"Failed to generate migration: {str(e)}")

    def apply_migrations(self, revision: str = "head") -> None:
        """Apply migrations (sync)."""
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            self.alembic_manager.upgrade(revision)
        except Exception as e:
            raise MigrationError(f"Failed to apply migrations: {str(e)}")

    async def apply_migrations_async(self, revision: str = "head") -> None:
        """Apply migrations (async)."""
        # Alembic doesn't natively support async, so we run it synchronously
        self.apply_migrations(revision)

    def downgrade_migration(self, revision: str = "-1") -> None:
        """Downgrade to a previous migration."""
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            self.alembic_manager.downgrade(revision)
        except Exception as e:
            raise MigrationError(f"Failed to downgrade migration: {str(e)}")

    def get_current_revision(self) -> Optional[str]:
        """Get current migration revision."""
        try:
            if not self.alembic_manager:
                return None
            return self.alembic_manager.current()
        except Exception as e:
            raise MigrationError(f"Failed to get current revision: {str(e)}")

    def stamp_migration(self, revision: str = "head") -> None:
        """
        Stamp database with a migration revision without running migrations.

        Useful when tables already exist and you want to mark them as migrated.
        """
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            self.alembic_manager.stamp(revision)
        except Exception as e:
            raise MigrationError(f"Failed to stamp migration: {str(e)}")

    def check_migration_sync(self) -> Dict[str, Any]:
        """
        Check if database schema is in sync with migration files.

        Returns dict with sync status information.
        """
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            return self.alembic_manager.check_migration_sync()
        except Exception as e:
            raise MigrationError(f"Failed to check migration sync: {str(e)}")

    def remove_duplicate_migrations(self) -> int:
        """
        Detect and remove duplicate migration files.

        Returns:
            Number of duplicate files removed
        """
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            return self.alembic_manager.remove_duplicate_migrations()
        except Exception as e:
            raise MigrationError(f"Failed to remove duplicate migrations: {str(e)}")

    def apply_migrations_smart(self, revision: str = "head", auto_stamp_on_conflict: bool = True) -> None:
        """
        Intelligently apply migrations with automatic handling of edge cases.

        This method will:
        - Automatically detect and remove duplicate migration files
        - Stamp database if tables exist but no migrations recorded
        - Auto-stamp on duplicate table errors (if auto_stamp_on_conflict=True)
        - Provide helpful error messages and suggestions

        Args:
            revision: Target revision (default: "head")
            auto_stamp_on_conflict: If True, automatically stamp database when duplicate
                                   table errors occur (default: True)
        """
        try:
            if not self.alembic_manager:
                raise MigrationError("Alembic manager not initialized. Call connect() first.")
            self.alembic_manager.smart_upgrade(revision, auto_stamp_on_conflict)
        except Exception as e:
            raise MigrationError(f"Failed to smart apply migrations: {str(e)}")

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations."""
        try:
            if not self.alembic_manager:
                return []
            return self.alembic_manager.history()
        except Exception as e:
            raise MigrationError(f"Failed to get migration history: {str(e)}")

    # ===== Table Operations =====

    def create_tables(self, models: Optional[List[Type]] = None) -> None:
        """Create tables from SQLAlchemy models (sync)."""
        try:
            from ..models.base import Base

            if models:
                # Create only specified models
                for model in models:
                    model.__table__.create(self.sync_engine, checkfirst=True)
            else:
                # Create all registered models
                Base.metadata.create_all(self.sync_engine)

        except Exception as e:
            raise TableError(f"Failed to create tables: {str(e)}")

    async def create_tables_async(self, models: Optional[List[Type]] = None) -> None:
        """Create tables from SQLAlchemy models (async)."""
        try:
            from ..models.base import Base

            async with self.async_engine.begin() as conn:
                if models:
                    for model in models:
                        await conn.run_sync(model.__table__.create, checkfirst=True)
                else:
                    await conn.run_sync(Base.metadata.create_all)

        except Exception as e:
            raise TableError(f"Failed to create tables: {str(e)}")

    def drop_tables(self, models: Optional[List[Type]] = None) -> None:
        """Drop tables (sync)."""
        try:
            from ..models.base import Base

            if models:
                for model in models:
                    model.__table__.drop(self.sync_engine, checkfirst=True)
            else:
                Base.metadata.drop_all(self.sync_engine)

        except Exception as e:
            raise TableError(f"Failed to drop tables: {str(e)}")

    async def drop_tables_async(self, models: Optional[List[Type]] = None) -> None:
        """Drop tables (async)."""
        try:
            from ..models.base import Base

            async with self.async_engine.begin() as conn:
                if models:
                    for model in models:
                        await conn.run_sync(model.__table__.drop, checkfirst=True)
                else:
                    await conn.run_sync(Base.metadata.drop_all)

        except Exception as e:
            raise TableError(f"Failed to drop tables: {str(e)}")

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists (sync)."""
        try:
            inspector = inspect(self.sync_engine)
            schema = self.config.schema if self.config.schema else None
            return table_name in inspector.get_table_names(schema=schema)
        except Exception as e:
            raise TableError(f"Failed to check if table exists: {str(e)}")

    async def table_exists_async(self, table_name: str) -> bool:
        """Check if table exists (async)."""
        try:
            async with self.async_engine.connect() as conn:
                def check(sync_conn):
                    inspector = inspect(sync_conn)
                    schema = self.config.schema if self.config.schema else None
                    return table_name in inspector.get_table_names(schema=schema)

                return await conn.run_sync(check)
        except Exception as e:
            raise TableError(f"Failed to check if table exists: {str(e)}")

    def list_tables(self) -> List[str]:
        """List all tables in database (sync)."""
        try:
            inspector = inspect(self.sync_engine)
            schema = self.config.schema if self.config.schema else None
            return inspector.get_table_names(schema=schema)
        except Exception as e:
            raise TableError(f"Failed to list tables: {str(e)}")

    def list_schemas(self) -> List[str]:
        """List all schemas in database (sync) - PostgreSQL only."""
        try:
            if self.config.provider != "postgresql":
                raise TableError("list_schemas() is only supported for PostgreSQL")

            inspector = inspect(self.sync_engine)
            return inspector.get_schema_names()
        except Exception as e:
            raise TableError(f"Failed to list schemas: {str(e)}")

    async def list_tables_async(self) -> List[str]:
        """List all tables in database (async)."""
        try:
            async with self.async_engine.connect() as conn:
                def get_tables(sync_conn):
                    inspector = inspect(sync_conn)
                    schema = self.config.schema if self.config.schema else None
                    return inspector.get_table_names(schema=schema)

                return await conn.run_sync(get_tables)
        except Exception as e:
            raise TableError(f"Failed to list tables: {str(e)}")

    async def list_schemas_async(self) -> List[str]:
        """List all schemas in database (async) - PostgreSQL only."""
        try:
            if self.config.provider != "postgresql":
                raise TableError("list_schemas_async() is only supported for PostgreSQL")

            async with self.async_engine.connect() as conn:
                def get_schemas(sync_conn):
                    inspector = inspect(sync_conn)
                    return inspector.get_schema_names()

                return await conn.run_sync(get_schemas)
        except Exception as e:
            raise TableError(f"Failed to list schemas: {str(e)}")

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information (sync)."""
        try:
            inspector = inspect(self.sync_engine)
            schema = self.config.schema if self.config.schema else None
            columns = inspector.get_columns(table_name, schema=schema)
            indexes = inspector.get_indexes(table_name, schema=schema)
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)

            return {
                "table_name": table_name,
                "schema": schema,
                "columns": columns,
                "indexes": indexes,
                "primary_key": pk_constraint,
                "foreign_keys": foreign_keys,
            }
        except Exception as e:
            raise TableError(f"Failed to describe table: {str(e)}")

    async def describe_table_async(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information (async)."""
        try:
            async with self.async_engine.connect() as conn:
                def get_schema(sync_conn):
                    inspector = inspect(sync_conn)
                    schema = self.config.schema if self.config.schema else None
                    return {
                        "table_name": table_name,
                        "schema": schema,
                        "columns": inspector.get_columns(table_name, schema=schema),
                        "indexes": inspector.get_indexes(table_name, schema=schema),
                        "primary_key": inspector.get_pk_constraint(table_name, schema=schema),
                        "foreign_keys": inspector.get_foreign_keys(table_name, schema=schema),
                    }

                return await conn.run_sync(get_schema)
        except Exception as e:
            raise TableError(f"Failed to describe table: {str(e)}")

    # ===== CRUD Operations - Create =====

    def insert(self, model: Type, data: Dict[str, Any]):
        """Insert single record (sync)."""
        try:
            with self.session_factory() as session:
                instance = model(**data)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return instance
        except Exception as e:
            raise QueryError(f"Failed to insert record: {str(e)}")

    async def insert_async(self, model: Type, data: Dict[str, Any]):
        """Insert single record (async)."""
        try:
            async with self.async_session_factory() as session:
                instance = model(**data)
                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                return instance
        except Exception as e:
            raise QueryError(f"Failed to insert record: {str(e)}")

    def insert_many(self, model: Type, data_list: List[Dict[str, Any]]) -> List:
        """Bulk insert records (sync)."""
        try:
            with self.session_factory() as session:
                instances = [model(**data) for data in data_list]
                session.add_all(instances)
                session.commit()
                for instance in instances:
                    session.refresh(instance)
                return instances
        except Exception as e:
            raise QueryError(f"Failed to bulk insert: {str(e)}")

    async def insert_many_async(self, model: Type, data_list: List[Dict[str, Any]]) -> List:
        """Bulk insert records (async)."""
        try:
            async with self.async_session_factory() as session:
                instances = [model(**data) for data in data_list]
                session.add_all(instances)
                await session.commit()
                for instance in instances:
                    await session.refresh(instance)
                return instances
        except Exception as e:
            raise QueryError(f"Failed to bulk insert: {str(e)}")

    # ===== CRUD Operations - Read =====

    def get_by_id(self, model: Type, id_value: Any) -> Optional:
        """Get record by primary key (sync)."""
        try:
            with self.session_factory() as session:
                return session.get(model, id_value)
        except Exception as e:
            raise QueryError(f"Failed to get record by ID: {str(e)}")

    async def get_by_id_async(self, model: Type, id_value: Any) -> Optional:
        """Get record by primary key (async)."""
        try:
            async with self.async_session_factory() as session:
                return await session.get(model, id_value)
        except Exception as e:
            raise QueryError(f"Failed to get record by ID: {str(e)}")

    def get_all(self, model: Type, limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Get all records with pagination (sync)."""
        try:
            with self.session_factory() as session:
                query = select(model)
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise QueryError(f"Failed to get all records: {str(e)}")

    async def get_all_async(self, model: Type, limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Get all records with pagination (async)."""
        try:
            async with self.async_session_factory() as session:
                query = select(model)
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise QueryError(f"Failed to get all records: {str(e)}")

    def query(self, model: Type, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Query records with filters (sync)."""
        try:
            with self.session_factory() as session:
                conditions = build_filter_clause(model, filters)
                query = select(model).where(*conditions)
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise QueryError(f"Failed to query records: {str(e)}")

    async def query_async(self, model: Type, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List:
        """Query records with filters (async)."""
        try:
            async with self.async_session_factory() as session:
                conditions = build_filter_clause(model, filters)
                query = select(model).where(*conditions)
                if offset:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise QueryError(f"Failed to query records: {str(e)}")

    def count(self, model: Type, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records (sync)."""
        try:
            with self.session_factory() as session:
                query = select(func.count()).select_from(model)
                if filters:
                    conditions = build_filter_clause(model, filters)
                    query = query.where(*conditions)
                result = session.execute(query)
                return result.scalar()
        except Exception as e:
            raise QueryError(f"Failed to count records: {str(e)}")

    async def count_async(self, model: Type, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records (async)."""
        try:
            async with self.async_session_factory() as session:
                query = select(func.count()).select_from(model)
                if filters:
                    conditions = build_filter_clause(model, filters)
                    query = query.where(*conditions)
                result = await session.execute(query)
                return result.scalar()
        except Exception as e:
            raise QueryError(f"Failed to count records: {str(e)}")

    # ===== CRUD Operations - Update =====

    def update(self, model: Type, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records matching filters (sync)."""
        try:
            with self.session_factory() as session:
                conditions = build_filter_clause(model, filters)
                stmt = update(model).where(*conditions).values(**updates)
                result = session.execute(stmt)
                session.commit()
                return result.rowcount
        except Exception as e:
            raise QueryError(f"Failed to update records: {str(e)}")

    async def update_async(self, model: Type, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records matching filters (async)."""
        try:
            async with self.async_session_factory() as session:
                conditions = build_filter_clause(model, filters)
                stmt = update(model).where(*conditions).values(**updates)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
        except Exception as e:
            raise QueryError(f"Failed to update records: {str(e)}")

    def update_by_id(self, model: Type, id_value: Any, updates: Dict[str, Any]) -> Optional:
        """Update single record by ID (sync)."""
        try:
            with self.session_factory() as session:
                instance = session.get(model, id_value)
                if instance:
                    for key, value in updates.items():
                        setattr(instance, key, value)
                    session.commit()
                    session.refresh(instance)
                return instance
        except Exception as e:
            raise QueryError(f"Failed to update record by ID: {str(e)}")

    async def update_by_id_async(self, model: Type, id_value: Any, updates: Dict[str, Any]) -> Optional:
        """Update single record by ID (async)."""
        try:
            async with self.async_session_factory() as session:
                instance = await session.get(model, id_value)
                if instance:
                    for key, value in updates.items():
                        setattr(instance, key, value)
                    await session.commit()
                    await session.refresh(instance)
                return instance
        except Exception as e:
            raise QueryError(f"Failed to update record by ID: {str(e)}")

    # ===== CRUD Operations - Delete =====

    def delete(self, model: Type, filters: Dict[str, Any]) -> int:
        """Delete records matching filters (sync)."""
        try:
            with self.session_factory() as session:
                conditions = build_filter_clause(model, filters)
                stmt = delete(model).where(*conditions)
                result = session.execute(stmt)
                session.commit()
                return result.rowcount
        except Exception as e:
            raise QueryError(f"Failed to delete records: {str(e)}")

    async def delete_async(self, model: Type, filters: Dict[str, Any]) -> int:
        """Delete records matching filters (async)."""
        try:
            async with self.async_session_factory() as session:
                conditions = build_filter_clause(model, filters)
                stmt = delete(model).where(*conditions)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount
        except Exception as e:
            raise QueryError(f"Failed to delete records: {str(e)}")

    def delete_by_id(self, model: Type, id_value: Any) -> bool:
        """Delete record by ID (sync)."""
        try:
            with self.session_factory() as session:
                instance = session.get(model, id_value)
                if instance:
                    session.delete(instance)
                    session.commit()
                    return True
                return False
        except Exception as e:
            raise QueryError(f"Failed to delete record by ID: {str(e)}")

    async def delete_by_id_async(self, model: Type, id_value: Any) -> bool:
        """Delete record by ID (async)."""
        try:
            async with self.async_session_factory() as session:
                instance = await session.get(model, id_value)
                if instance:
                    await session.delete(instance)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            raise QueryError(f"Failed to delete record by ID: {str(e)}")

    def truncate(self, model: Type) -> None:
        """Truncate table (sync)."""
        try:
            table_name = get_table_name(model)
            with self.sync_engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                conn.commit()
        except Exception as e:
            raise QueryError(f"Failed to truncate table: {str(e)}")

    async def truncate_async(self, model: Type) -> None:
        """Truncate table (async)."""
        try:
            table_name = get_table_name(model)
            async with self.async_engine.connect() as conn:
                await conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                await conn.commit()
        except Exception as e:
            raise QueryError(f"Failed to truncate table: {str(e)}")

    # ===== Raw SQL Execution =====

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query (sync)."""
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                conn.commit()
                return result
        except Exception as e:
            raise QueryError(f"Failed to execute query: {str(e)}")

    async def execute_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query (async)."""
        try:
            async with self.async_engine.connect() as conn:
                result = await conn.execute(text(sql), params or {})
                await conn.commit()
                return result
        except Exception as e:
            raise QueryError(f"Failed to execute query: {str(e)}")

    def fetch_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result as dictionary (sync)."""
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
                return None
        except Exception as e:
            raise QueryError(f"Failed to fetch one: {str(e)}")

    async def fetch_one_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result as dictionary (async)."""
        try:
            async with self.async_engine.connect() as conn:
                result = await conn.execute(text(sql), params or {})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
                return None
        except Exception as e:
            raise QueryError(f"Failed to fetch one: {str(e)}")

    def fetch_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results as dictionaries (sync)."""
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            raise QueryError(f"Failed to fetch all: {str(e)}")

    async def fetch_all_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results as dictionaries (async)."""
        try:
            async with self.async_engine.connect() as conn:
                result = await conn.execute(text(sql), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            raise QueryError(f"Failed to fetch all: {str(e)}")

    # ===== Transaction Management =====

    @contextmanager
    def begin_transaction(self):
        """Begin transaction (sync)."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise TransactionError(f"Transaction failed: {str(e)}")
        finally:
            session.close()

    @asynccontextmanager
    async def begin_transaction_async(self):
        """Begin transaction (async)."""
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise TransactionError(f"Transaction failed: {str(e)}")
        finally:
            await session.close()

    def commit(self) -> None:
        """Commit current transaction (sync)."""
        if self._current_session:
            try:
                self._current_session.commit()
            except Exception as e:
                raise TransactionError(f"Failed to commit: {str(e)}")

    async def commit_async(self) -> None:
        """Commit current transaction (async)."""
        if self._current_async_session:
            try:
                await self._current_async_session.commit()
            except Exception as e:
                raise TransactionError(f"Failed to commit: {str(e)}")

    def rollback(self) -> None:
        """Rollback current transaction (sync)."""
        if self._current_session:
            try:
                self._current_session.rollback()
            except Exception as e:
                raise TransactionError(f"Failed to rollback: {str(e)}")

    async def rollback_async(self) -> None:
        """Rollback current transaction (async)."""
        if self._current_async_session:
            try:
                await self._current_async_session.rollback()
            except Exception as e:
                raise TransactionError(f"Failed to rollback: {str(e)}")
