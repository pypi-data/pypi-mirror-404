"""
In-Memory Storage Backend

Simple, fast, ephemeral storage using Python dictionaries.
Perfect for development, testing, and non-persistent use cases.

Benefits:
- Zero dependencies
- Fastest performance (nanoseconds)
- No setup required
- Thread-safe with basic locking

Drawbacks:
- Data lost on restart
- Not suitable for production
- Limited to single process
"""

import logging
from threading import Lock
from typing import Any

from .base import StorageBackend

logger = logging.getLogger(__name__)


class InMemoryBackend(StorageBackend):
    """
    In-memory storage backend using Python dict.

    All data is stored in memory and lost when process exits.
    Thread-safe using locks.

    Example:
        backend = InMemoryBackend()
        backend.save("user_123", {"name": "John", "age": 30})
        data = backend.load("user_123")
        print(data)  # {"name": "John", "age": 30}
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._storage: dict[str, Any] = {}
        self._lock = Lock()
        logger.info("Initialized InMemoryBackend")

    def save(self, key: str, data: Any, **kwargs: Any) -> bool:
        """Save data to memory."""
        try:
            with self._lock:
                self._storage[key] = data
            logger.debug(f"Saved key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save key {key}: {e}")
            return False

    def load(self, key: str, **kwargs: Any) -> Any | None:
        """Load data from memory."""
        try:
            with self._lock:
                data = self._storage.get(key)
            if data is not None:
                logger.debug(f"Loaded key: {key}")
            else:
                logger.debug(f"Key not found: {key}")
            return data
        except Exception as e:
            logger.error(f"Failed to load key {key}: {e}")
            return None

    def delete(self, key: str, **kwargs: Any) -> bool:
        """Delete data from memory."""
        try:
            with self._lock:
                if key in self._storage:
                    del self._storage[key]
                    logger.debug(f"Deleted key: {key}")
                    return True
                else:
                    logger.debug(f"Key not found for deletion: {key}")
                    return False
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False

    def clear(self, **kwargs: Any) -> bool:
        """Clear all data from memory."""
        try:
            with self._lock:
                count = len(self._storage)
                self._storage.clear()
            logger.info(f"Cleared {count} keys from memory")
            return True
        except Exception as e:
            logger.error(f"Failed to clear storage: {e}")
            return False

    def exists(self, key: str, **kwargs: Any) -> bool:
        """Check if key exists in memory."""
        with self._lock:
            return key in self._storage

    def list_keys(self, prefix: str | None = None, **kwargs: Any) -> list[str]:
        """List all keys in memory."""
        with self._lock:
            keys = list(self._storage.keys())

        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]

        return keys

    def __len__(self) -> int:
        """Return number of items in storage."""
        with self._lock:
            return len(self._storage)

    def __repr__(self) -> str:
        """String representation."""
        with self._lock:
            count = len(self._storage)
        return f"InMemoryBackend(items={count})"
