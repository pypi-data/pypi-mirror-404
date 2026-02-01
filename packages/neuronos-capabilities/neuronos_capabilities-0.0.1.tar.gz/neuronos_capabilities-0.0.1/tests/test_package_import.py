"""Test top-level package imports and structure."""
import pytest


def test_import_sqlmanager_from_root():
    """Test that SQLManager can be imported from package root."""
    from neuronos_capabilities import SQLManager
    assert SQLManager is not None
    assert hasattr(SQLManager, '__init__')


def test_import_version():
    """Test that package version is accessible."""
    from neuronos_capabilities import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__.split('.')) == 3  # Semver format


def test_sqlmanager_subpackage_import():
    """Test that SQLManager can be imported from subpackage."""
    from neuronos_capabilities.SQLManager import SQLManager
    assert SQLManager is not None


def test_base_model_import():
    """Test that Base model can be imported for user models."""
    from neuronos_capabilities.SQLManager import Base
    assert Base is not None


def test_sqlconfig_import():
    """Test that SQLConfig can be imported."""
    from neuronos_capabilities.SQLManager import SQLConfig
    assert SQLConfig is not None


def test_exceptions_import():
    """Test that all exceptions can be imported."""
    from neuronos_capabilities.SQLManager import (
        SQLManagerError,
        ConfigurationError,
        ConnectionError,
        QueryError,
        MigrationError,
        TransactionError,
        TableError,
        ModelError
    )

    # Verify inheritance hierarchy
    assert issubclass(ConfigurationError, SQLManagerError)
    assert issubclass(ConnectionError, SQLManagerError)
    assert issubclass(QueryError, SQLManagerError)
    assert issubclass(MigrationError, SQLManagerError)
    assert issubclass(TransactionError, SQLManagerError)
    assert issubclass(TableError, SQLManagerError)
    assert issubclass(ModelError, SQLManagerError)


def test_package_all_exports():
    """Test that __all__ is properly defined."""
    from neuronos_capabilities import __all__

    assert "SQLManager" in __all__
    assert "__version__" in __all__


def test_sqlmanager_subpackage_all_exports():
    """Test that SQLManager subpackage __all__ is properly defined."""
    from neuronos_capabilities.SQLManager import __all__

    expected_exports = [
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

    for export in expected_exports:
        assert export in __all__, f"{export} not in __all__"
