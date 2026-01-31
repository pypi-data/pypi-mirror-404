"""
Storage Backends Package

This package provides pluggable storage backends for ToolWeaver.

Usage:
    from orchestrator._internal.backends import get_storage_backend

    # In-memory (default)
    backend = get_storage_backend("memory")

    # File-based (persistent)
    backend = get_storage_backend("file", storage_path=".toolweaver")

    # Redis (Phase 5, distributed)
    backend = get_storage_backend("redis", redis_url="redis://localhost:6379")
"""

# Re-export from storage backend (for backwards compatibility)
from orchestrator._internal.backends.storage.base import (
    StorageBackend,
    StorageError,
    get_storage_backend,
)
from orchestrator._internal.backends.storage.file import FileBackend
from orchestrator._internal.backends.storage.memory import InMemoryBackend

__all__ = [
    "StorageBackend",
    "StorageError",
    "get_storage_backend",
    "InMemoryBackend",
    "FileBackend",
]
