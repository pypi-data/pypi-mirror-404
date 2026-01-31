"""
Storage Backend Abstract Base Class

This module defines the abstract interface for storage backends.
Following the pluggable architecture pattern (LiteLLM-style).

All storage backends (Memory, File, Redis, PostgreSQL) must implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, cast

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    This interface defines the contract that all storage implementations must follow.
    Implementations can use any storage mechanism (memory, file, database, etc.).

    Benefits:
    - Zero forced dependencies (users choose their backend)
    - Easy to test (mock backends)
    - Extensible (users can implement custom backends)
    - Swappable (change backend without changing code)

    Example:
        class MyCustomBackend(StorageBackend):
            def save(self, key: str, data: Any) -> bool:
                # Your custom implementation
                pass

            def load(self, key: str) -> Optional[Any]:
                # Your custom implementation
                pass

            def delete(self, key: str) -> bool:
                # Your custom implementation
                pass

            def clear(self) -> bool:
                # Your custom implementation
                pass
    """

    @abstractmethod
    def save(self, key: str, data: Any, **kwargs: Any) -> bool:
        """
        Save data to storage.

        Args:
            key: Unique identifier for the data
            data: Data to store (any serializable type)
            **kwargs: Backend-specific options

        Returns:
            True if successful, False otherwise

        Raises:
            StorageError: If save operation fails critically
        """
        pass

    @abstractmethod
    def load(self, key: str, **kwargs: Any) -> Any | None:
        """
        Load data from storage.

        Args:
            key: Unique identifier for the data
            **kwargs: Backend-specific options

        Returns:
            The stored data, or None if not found

        Raises:
            StorageError: If load operation fails critically
        """
        pass

    @abstractmethod
    def delete(self, key: str, **kwargs: Any) -> bool:
        """
        Delete data from storage.

        Args:
            key: Unique identifier for the data
            **kwargs: Backend-specific options

        Returns:
            True if deleted, False if not found

        Raises:
            StorageError: If delete operation fails critically
        """
        pass

    @abstractmethod
    def clear(self, **kwargs: Any) -> bool:
        """
        Clear all data from storage.

        Args:
            **kwargs: Backend-specific options (e.g., tenant_id for multi-tenant)

        Returns:
            True if successful, False otherwise

        Raises:
            StorageError: If clear operation fails critically
        """
        pass

    @abstractmethod
    def exists(self, key: str, **kwargs: Any) -> bool:
        """
        Check if key exists in storage.

        Args:
            key: Unique identifier to check
            **kwargs: Backend-specific options

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str | None = None, **kwargs: Any) -> list[str]:
        """
        List all keys in storage.

        Args:
            prefix: Optional prefix to filter keys
            **kwargs: Backend-specific options

        Returns:
            List of keys
        """
        pass


class StorageError(Exception):
    """
    Exception raised for storage backend errors.

    Use this for critical errors that should stop execution.
    For recoverable errors, return False or None from methods.
    """

    pass


# Factory function for backend selection
def get_storage_backend(backend_type: str = "memory", **kwargs: Any) -> StorageBackend:
    """
    Factory function to create storage backend instances.

    Args:
        backend_type: Type of backend ("memory", "file", "redis", "postgresql")
        **kwargs: Backend-specific configuration

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If backend_type is unknown
        ImportError: If backend dependencies are missing

    Example:
        # In-memory backend (default, zero deps)
        backend = get_storage_backend("memory")

        # File backend (persistent, zero deps)
        backend = get_storage_backend("file", storage_path=".toolweaver/storage")

        # Redis backend (distributed, requires redis package)
        backend = get_storage_backend("redis", redis_url="redis://localhost:6379")
    """
    # Import here to avoid circular dependencies
    from .file import FileBackend
    from .memory import InMemoryBackend

    backends = {
        "memory": InMemoryBackend,
        "file": FileBackend,
    }

    # Phase 5: Add enterprise backends
    # try:
    #     from .redis import RedisBackend
    #     backends["redis"] = RedisBackend
    # except ImportError:
    #     pass

    # try:
    #     from .postgresql import PostgreSQLBackend
    #     backends["postgresql"] = PostgreSQLBackend
    # except ImportError:
    #     pass

    backend_class = backends.get(backend_type)
    if not backend_class:
        available = ", ".join(backends.keys())
        raise ValueError(f"Unknown backend type: {backend_type}. Available backends: {available}")

    try:
        return cast(StorageBackend, backend_class(**kwargs))
    except Exception as e:
        raise StorageError(f"Failed to initialize {backend_type} backend: {e}") from e
