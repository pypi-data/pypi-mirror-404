"""
SQLManager - Database Management Capability for NeuronOS.

A comprehensive, provider-agnostic SQL database management capability following
hexagonal architecture principles. Supports SQLAlchemy ORM, Alembic migrations,
connection pooling, and both synchronous and asynchronous operations.

Example:
    from neuronos_capabilities import SQLManager
    # OR
    from neuronos_capabilities.SQLManager import SQLManager

    config = {
        "host": "localhost",
        "database": "myapp",
        "user": "postgres",
        "password": "secret"
    }

    with SQLManager(config) as db:
        user = db.insert(User, {"name": "Alice", "email": "alice@example.com"})
        users = db.query(User, {"name": "Alice"})
"""

from .sql_manager import SQLManager
from .models.base import Base
from .config.sql_config import SQLConfig
from .exceptions.sql_exceptions import (
    SQLManagerError,
    ConfigurationError,
    ConnectionError,
    QueryError,
    MigrationError,
    TransactionError,
    TableError,
    ModelError
)

__all__ = [
    "SQLManager",
    "Base",
    "SQLConfig",
    "SQLManagerError",
    "ConfigurationError",
    "ConnectionError",
    "QueryError",
    "MigrationError",
    "TransactionError",
    "TableError",
    "ModelError"
]

__version__ = "1.0.0"
