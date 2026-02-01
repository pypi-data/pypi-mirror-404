"""
Query building helper utilities for SQLManager.

This module provides utility functions for building SQL queries and
working with SQLAlchemy models.
"""

from typing import Any, Dict, List, Optional, Type
from sqlalchemy import inspect, select, update, delete, func
from sqlalchemy.orm import DeclarativeBase


def build_filter_clause(model: Type[DeclarativeBase], filters: Dict[str, Any]):
    """
    Build a SQLAlchemy filter clause from a dictionary of filters.

    Args:
        model: SQLAlchemy model class
        filters: Dictionary of column names and values to filter by

    Returns:
        List of filter conditions for use in where() clauses

    Example:
        filters = {"name": "John", "age": 30}
        conditions = build_filter_clause(User, filters)
        query = select(User).where(*conditions)
    """
    conditions = []
    for key, value in filters.items():
        if hasattr(model, key):
            column = getattr(model, key)
            conditions.append(column == value)
    return conditions


def get_primary_key_name(model: Type[DeclarativeBase]) -> str:
    """
    Get the primary key column name for a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        Name of the primary key column

    Raises:
        ValueError: If model has no primary key or multiple primary keys
    """
    mapper = inspect(model)
    primary_keys = [key.name for key in mapper.primary_key]

    if len(primary_keys) == 0:
        raise ValueError(f"Model {model.__name__} has no primary key")
    if len(primary_keys) > 1:
        raise ValueError(
            f"Model {model.__name__} has composite primary key, not supported"
        )

    return primary_keys[0]


def get_primary_key_column(model: Type[DeclarativeBase]):
    """
    Get the primary key column object for a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        Primary key column object
    """
    pk_name = get_primary_key_name(model)
    return getattr(model, pk_name)


def get_table_name(model: Type[DeclarativeBase]) -> str:
    """
    Get the table name for a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        Table name as string
    """
    return model.__tablename__


def model_to_dict(instance: DeclarativeBase, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy model instance to a dictionary.

    Args:
        instance: SQLAlchemy model instance
        exclude: List of column names to exclude from the dictionary

    Returns:
        Dictionary representation of the model instance
    """
    exclude = exclude or []
    mapper = inspect(instance.__class__)
    result = {}

    for column in mapper.columns:
        if column.name not in exclude:
            result[column.name] = getattr(instance, column.name)

    return result


def dict_to_model(model: Type[DeclarativeBase], data: Dict[str, Any]) -> DeclarativeBase:
    """
    Create a model instance from a dictionary.

    Args:
        model: SQLAlchemy model class
        data: Dictionary of column names and values

    Returns:
        New model instance
    """
    return model(**data)


def paginate_query(query, page: int = 1, page_size: int = 20):
    """
    Apply pagination to a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated query object
    """
    offset = (page - 1) * page_size
    return query.limit(page_size).offset(offset)


def get_column_names(model: Type[DeclarativeBase]) -> List[str]:
    """
    Get all column names for a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        List of column names
    """
    mapper = inspect(model)
    return [column.name for column in mapper.columns]


def get_relationship_names(model: Type[DeclarativeBase]) -> List[str]:
    """
    Get all relationship names for a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        List of relationship names
    """
    mapper = inspect(model)
    return [rel.key for rel in mapper.relationships]


def validate_model_data(model: Type[DeclarativeBase], data: Dict[str, Any]) -> bool:
    """
    Validate that data dictionary contains valid column names for the model.

    Args:
        model: SQLAlchemy model class
        data: Dictionary of column names and values

    Returns:
        True if all keys in data are valid column names

    Raises:
        ValueError: If data contains invalid column names
    """
    valid_columns = get_column_names(model)
    invalid_keys = [key for key in data.keys() if key not in valid_columns]

    if invalid_keys:
        raise ValueError(
            f"Invalid column names for {model.__name__}: {', '.join(invalid_keys)}"
        )

    return True


class PaginationResult:
    """
    Result object for paginated queries.

    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
    """

    def __init__(
        self,
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert pagination result to dictionary."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next(),
            "has_prev": self.has_prev(),
        }
