"""
File-Based Storage Backend

Persistent storage using JSON files in a directory structure.
Perfect for single-machine deployments without external dependencies.

Benefits:
- Data persists across restarts
- Human-readable JSON format
- No external dependencies
- Easy to backup/restore

Drawbacks:
- Slower than in-memory (milliseconds)
- Not suitable for high-concurrency
- File system limits apply
- Manual cleanup needed
"""

import json
import logging
from pathlib import Path
from typing import Any

from .base import StorageBackend, StorageError

logger = logging.getLogger(__name__)


class FileBackend(StorageBackend):
    """
    File-based storage backend using JSON files.

    Each key is stored as a separate JSON file in the storage directory.
    Creates directory structure automatically.

    Example:
        backend = FileBackend(storage_path=".toolweaver/storage")
        backend.save("user_123", {"name": "John", "age": 30})
        data = backend.load("user_123")
        print(data)  # {"name": "John", "age": 30}
    """

    def __init__(self, storage_path: str = ".toolweaver/storage") -> None:
        """
        Initialize file-based storage.

        Args:
            storage_path: Directory path for storing files (created if missing)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FileBackend at: {self.storage_path}")

    def _get_file_path(self, key: str) -> Path:
        """Convert key to file path, sanitizing special characters."""
        # Replace special chars with underscores for safe filenames
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self.storage_path / f"{safe_key}.json"

    def save(self, key: str, data: Any, **kwargs: Any) -> bool:
        """Save data to JSON file."""
        try:
            file_path = self._get_file_path(key)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved key: {key} to {file_path}")
            return True
        except (OSError, TypeError) as e:
            logger.error(f"Failed to save key {key}: {e}")
            raise StorageError(f"Failed to save key {key}: {e}") from None

    def load(self, key: str, **kwargs: Any) -> Any | None:
        """Load data from JSON file."""
        try:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                logger.debug(f"Key not found: {key}")
                return None

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"Loaded key: {key} from {file_path}")
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load key {key}: {e}")
            raise StorageError(f"Failed to load key {key}: {e}") from None

    def delete(self, key: str, **kwargs: Any) -> bool:
        """Delete JSON file."""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted key: {key}")
                return True
            else:
                logger.debug(f"Key not found for deletion: {key}")
                return False
        except OSError as e:
            logger.error(f"Failed to delete key {key}: {e}")
            raise StorageError(f"Failed to delete key {key}: {e}") from None

    def clear(self, **kwargs: Any) -> bool:
        """Delete all JSON files in storage directory."""
        try:
            count = 0
            for file_path in self.storage_path.glob("*.json"):
                file_path.unlink()
                count += 1
            logger.info(f"Cleared {count} files from {self.storage_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to clear storage: {e}")
            raise StorageError(f"Failed to clear storage: {e}") from None

    def exists(self, key: str, **kwargs: Any) -> bool:
        """Check if JSON file exists."""
        file_path = self._get_file_path(key)
        return file_path.exists()

    def list_keys(self, prefix: str | None = None, **kwargs: Any) -> list[str]:
        """List all keys (JSON files without .json extension)."""
        keys = []
        for file_path in self.storage_path.glob("*.json"):
            key = file_path.stem  # Filename without .json
            if prefix is None or key.startswith(prefix):
                keys.append(key)
        return keys

    def __repr__(self) -> str:
        """String representation."""
        count = len(list(self.storage_path.glob("*.json")))
        return f"FileBackend(path={self.storage_path}, items={count})"
