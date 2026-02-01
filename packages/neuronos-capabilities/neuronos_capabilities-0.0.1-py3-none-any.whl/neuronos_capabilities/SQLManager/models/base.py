"""
Base model class for SQLAlchemy ORM.

This module provides the declarative base class that all user-defined models
should inherit from.
"""

from sqlalchemy.orm import DeclarativeBase, registry
from sqlalchemy import MetaData
from typing import Optional


# Naming convention for constraints (helps with Alembic migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Global variable to hold the current schema
_current_schema: Optional[str] = None


def set_schema(schema: Optional[str]) -> None:
    """
    Set the default schema for all models.

    This should be called before defining models or creating tables.

    Args:
        schema: Schema name (e.g., "app_schema", "analytics"). None uses database default (typically "public" for PostgreSQL).
    """
    global _current_schema
    _current_schema = schema


def get_schema() -> Optional[str]:
    """
    Get the current default schema.

    Returns:
        Current schema name or None
    """
    return _current_schema


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All user-defined models should inherit from this class.

    Schema Support:
        You can specify a schema in two ways:

        1. Set globally using set_schema() before defining models:
            from SQLManager.models.base import Base, set_schema
            set_schema("my_schema")

        2. Set per-model using __table_args__:
            class User(Base):
                __tablename__ = "users"
                __table_args__ = {"schema": "my_schema"}

    Example:
        from SQLManager.models.base import Base
        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import String

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
            email: Mapped[str] = mapped_column(String(255), unique=True)
    """

    def __init_subclass__(cls, **kwargs):
        """
        Automatically set schema for child classes if not explicitly set.
        """
        super().__init_subclass__(**kwargs)

        # Only apply if schema is set globally and model doesn't have explicit schema
        if _current_schema and hasattr(cls, '__tablename__'):
            # Check if __table_args__ already exists
            if hasattr(cls, '__table_args__'):
                table_args = cls.__table_args__
                # If it's a dict and doesn't have schema, add it
                if isinstance(table_args, dict) and 'schema' not in table_args:
                    cls.__table_args__ = {**table_args, 'schema': _current_schema}
                # If it's a tuple, check the last element (should be dict)
                elif isinstance(table_args, tuple):
                    if len(table_args) > 0 and isinstance(table_args[-1], dict):
                        if 'schema' not in table_args[-1]:
                            cls.__table_args__ = table_args[:-1] + ({**table_args[-1], 'schema': _current_schema},)
                    else:
                        cls.__table_args__ = table_args + ({'schema': _current_schema},)
            else:
                # No __table_args__ exists, create it with schema
                cls.__table_args__ = {'schema': _current_schema}

    def __repr__(self) -> str:
        """String representation of the model instance."""
        class_name = self.__class__.__name__
        attrs = ", ".join(
            f"{key}={value!r}"
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        )
        return f"{class_name}({attrs})"


# Apply naming convention to the Base metadata after class definition
Base.metadata.naming_convention = convention
