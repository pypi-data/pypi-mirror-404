"""
Configuration module for SQLManager capability.

This module defines the SQLConfig dataclass for managing database connection
and behavior settings.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SQLConfig:
    """
    Configuration for SQL database connection and behavior.

    Attributes:
        provider: Database provider (e.g., "postgresql", "mysql", "sqlite")
        host: Database server host
        port: Database server port
        database: Database name (required)
        user: Database username (required)
        password: Database password

        schema: Database schema for table organization (PostgreSQL: defaults to "public")

        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of overflow connections beyond pool_size
        pool_timeout: Connection timeout in seconds
        pool_recycle: Recycle connections after N seconds to handle stale connections

        echo_sql: If True, log all SQL statements
        autocommit: If True, automatically commit after each statement

        ssl_mode: SSL mode for connection (e.g., "require", "prefer", "disable")
        ssl_cert: Path to SSL certificate file
        ssl_key: Path to SSL key file
        ssl_ca: Path to SSL CA certificate file

        migrations_directory: Directory for Alembic migrations
    """

    # Connection parameters (required)
    database: str = ""
    user: str = ""

    # Connection parameters (optional)
    provider: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    password: str = ""

    # Schema settings
    schema: Optional[str] = None  # Database schema (PostgreSQL: defaults to "public", can be custom like "app_schema")

    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # Behavior settings
    echo_sql: bool = False
    autocommit: bool = False

    # SSL settings (optional)
    ssl_mode: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # Alembic settings
    migrations_directory: str = "migrations"

    def __post_init__(self):
        """
        Validate configuration after initialization.

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not self.database:
            raise ValueError("Database name is required")
        if not self.user:
            raise ValueError("User is required")

        if self.pool_size <= 0:
            raise ValueError("pool_size must be greater than 0")
        if self.max_overflow < 0:
            raise ValueError("max_overflow must be >= 0")
        if self.pool_timeout <= 0:
            raise ValueError("pool_timeout must be greater than 0")
        if self.pool_recycle <= 0:
            raise ValueError("pool_recycle must be greater than 0")

        # Validate provider
        valid_providers = ["postgresql", "mysql", "sqlite", "sqlserver"]
        if self.provider.lower() not in valid_providers:
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                f"Supported providers: {', '.join(valid_providers)}"
            )

        # Normalize provider name
        self.provider = self.provider.lower()

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "provider": self.provider,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "schema": self.schema,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo_sql": self.echo_sql,
            "autocommit": self.autocommit,
            "ssl_mode": self.ssl_mode,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key,
            "ssl_ca": self.ssl_ca,
            "migrations_directory": self.migrations_directory,
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "SQLConfig":
        """
        Create SQLConfig from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            SQLConfig instance
        """
        return cls(**config_dict)

    def get_connection_string(self, async_mode: bool = False) -> str:
        """
        Generate connection string from configuration.

        Args:
            async_mode: If True, generate async connection string

        Returns:
            SQLAlchemy connection string
        """
        if self.provider == "postgresql":
            driver = "asyncpg" if async_mode else "psycopg2"
            prefix = f"postgresql+{driver}"
        elif self.provider == "mysql":
            driver = "aiomysql" if async_mode else "pymysql"
            prefix = f"mysql+{driver}"
        elif self.provider == "sqlite":
            driver = "aiosqlite" if async_mode else ""
            prefix = f"sqlite+{driver}" if driver else "sqlite"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Build connection string
        if self.provider == "sqlite":
            return f"{prefix}:///{self.database}"
        else:
            password_part = f":{self.password}" if self.password else ""
            return f"{prefix}://{self.user}{password_part}@{self.host}:{self.port}/{self.database}"
