"""
Custom exceptions for SQLManager capability.

This module defines exception classes for better error handling and
debugging of database operations.
"""


class SQLManagerError(Exception):
    """
    Base exception for all SQLManager errors.

    All other exceptions inherit from this class, allowing users to catch
    all SQLManager-related errors with a single except clause.
    """

    pass


class ConnectionError(SQLManagerError):
    """
    Raised when database connection fails or is lost.

    Examples:
        - Failed to connect to database server
        - Connection timeout
        - Authentication failure
        - Connection lost during operation
    """

    pass


class QueryError(SQLManagerError):
    """
    Raised when a database query fails to execute.

    Examples:
        - SQL syntax error
        - Invalid table or column name
        - Query timeout
        - Constraint violation
    """

    pass


class MigrationError(SQLManagerError):
    """
    Raised when a migration operation fails.

    Examples:
        - Failed to initialize Alembic
        - Failed to generate migration
        - Failed to apply migration
        - Failed to downgrade migration
        - Migration conflict
    """

    pass


class ConfigurationError(SQLManagerError):
    """
    Raised when configuration is invalid or incomplete.

    Examples:
        - Missing required configuration parameters
        - Invalid configuration values
        - Unsupported database provider
        - Invalid connection string
    """

    pass


class TransactionError(SQLManagerError):
    """
    Raised when transaction operations fail.

    Examples:
        - Failed to begin transaction
        - Failed to commit transaction
        - Failed to rollback transaction
        - Transaction deadlock
        - Transaction conflict
    """

    pass


class TableError(SQLManagerError):
    """
    Raised when table operations fail.

    Examples:
        - Table does not exist
        - Failed to create table
        - Failed to drop table
        - Table already exists
    """

    pass


class ModelError(SQLManagerError):
    """
    Raised when model operations fail.

    Examples:
        - Invalid model class
        - Model not registered
        - Model metadata not found
        - Primary key not defined
    """

    pass
