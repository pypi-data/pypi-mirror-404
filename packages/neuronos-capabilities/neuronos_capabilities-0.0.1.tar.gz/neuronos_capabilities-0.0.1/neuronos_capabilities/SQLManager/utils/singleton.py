"""
Singleton registry for managing database connection pools.

This module implements a thread-safe singleton pattern to prevent connection
saturation by reusing connection pools across multiple SQLManager instances
with the same configuration.
"""

import threading
from typing import Any, Dict, Optional


class SingletonRegistry:
    """
    Thread-safe singleton registry for managing database adapters.

    This registry ensures that multiple SQLManager instances with the same
    configuration share the same underlying database adapter and connection pool,
    preventing connection saturation.

    Attributes:
        _registry: Dictionary mapping configuration keys to adapter instances
        _lock: Threading lock for thread-safe access to the registry
    """

    def __init__(self):
        """Initialize the singleton registry with an empty dictionary and lock."""
        self._registry: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(self, key: str, instance: Any) -> None:
        """
        Register an adapter instance with a unique key.

        Args:
            key: Unique identifier for the adapter (typically a connection string)
            instance: The adapter instance to register

        Thread-safe: Acquires lock before modifying the registry
        """
        with self._lock:
            self._registry[key] = instance

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an adapter instance by its key.

        Args:
            key: The unique identifier for the adapter

        Returns:
            The adapter instance if found, None otherwise

        Thread-safe: Acquires lock before accessing the registry
        """
        with self._lock:
            return self._registry.get(key)

    def unregister(self, key: str) -> None:
        """
        Remove an adapter instance from the registry.

        Args:
            key: The unique identifier for the adapter to remove

        Thread-safe: Acquires lock before modifying the registry
        """
        with self._lock:
            if key in self._registry:
                del self._registry[key]

    def clear(self) -> None:
        """
        Clear all registered adapter instances.

        This is useful for cleanup or testing purposes.

        Thread-safe: Acquires lock before clearing the registry
        """
        with self._lock:
            self._registry.clear()

    def contains(self, key: str) -> bool:
        """
        Check if an adapter with the given key exists in the registry.

        Args:
            key: The unique identifier to check

        Returns:
            True if the key exists in the registry, False otherwise

        Thread-safe: Acquires lock before checking the registry
        """
        with self._lock:
            return key in self._registry

    def size(self) -> int:
        """
        Get the number of registered adapters.

        Returns:
            The number of adapters in the registry

        Thread-safe: Acquires lock before accessing the registry
        """
        with self._lock:
            return len(self._registry)

    def keys(self) -> list:
        """
        Get a list of all registered keys.

        Returns:
            List of all keys in the registry

        Thread-safe: Acquires lock before accessing the registry
        """
        with self._lock:
            return list(self._registry.keys())
