"""
Models package for SQLManager.

This package contains the base model class and schema management utilities.
"""

from .base import Base, set_schema, get_schema

__all__ = ["Base", "set_schema", "get_schema"]
