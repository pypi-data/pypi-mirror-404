"""
Memory storage provider adapters for stdlib memory_put/get tools.

Similar to search/fetch providers, this module provides a unified interface for
different storage backends (in-memory, Redis, SQLite, PostgreSQL, etc.).

Users can add custom providers by:
1. Subclassing MemoryProvider
2. Implementing the put(), get(), and delete() methods
3. Registering with register_memory_provider()

Example custom provider:
    class RedisProvider(MemoryProvider):
        def __init__(self) -> None:
            import redis
            self.client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            )

        def put(self, key: str, value: Any, ttl_s: int | None) -> dict:
            self.client.set(key, json.dumps(value), ex=ttl_s)
            return {"key": key, "stored": True, "ttl_s": ttl_s}

        def get(self, key: str) -> dict:
            data = self.client.get(key)
            if data:
                return {"key": key, "value": json.loads(data), "found": True}
            return {"key": key, "found": False}

    register_memory_provider("redis", RedisProvider)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available memory providers
_MEMORY_PROVIDERS: dict[str, type[MemoryProvider]] = {}


# ============================================================
# Base Memory Provider Interface
# ============================================================


class MemoryProvider(ABC):
    """
    Base class for memory storage providers.

    Subclass this to add support for different backends (Redis, SQLite, PostgreSQL, etc.).
    """

    @abstractmethod
    def put(self, key: str, value: Any, ttl_s: int | None) -> dict[str, Any]:
        """
        Store a value with optional TTL.

        Args:
            key: Storage key (already validated/truncated)
            value: Value to store (dict or string, already validated)
            ttl_s: Time-to-live in seconds (already capped) or None

        Returns:
            Dictionary containing:
            - key (str): The storage key
            - stored (bool): Whether storage succeeded
            - ttl_s (int | None): The TTL applied

        Raises:
            Exception: If storage fails (caught by caller)
        """
        pass

    @abstractmethod
    def get(self, key: str) -> dict[str, Any]:
        """
        Retrieve a value by key.

        Args:
            key: Storage key (already validated/truncated)

        Returns:
            Dictionary containing:
            - key (str): The storage key
            - value (Any): The stored value (if found)
            - found (bool): Whether the key was found

        Raises:
            Exception: If retrieval fails (caught by caller)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> dict[str, Any]:
        """
        Delete a value by key.

        Args:
            key: Storage key (already validated/truncated)

        Returns:
            Dictionary containing:
            - key (str): The storage key
            - deleted (bool): Whether the key was deleted

        Raises:
            Exception: If deletion fails (caught by caller)
        """
        pass


# ============================================================
# In-Memory Provider (Default)
# ============================================================


class InMemoryProvider(MemoryProvider):
    """
    In-memory storage using a dict (session-scoped).

    Data is lost when the process ends. Suitable for temporary session data.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    def put(self, key: str, value: Any, ttl_s: int | None) -> dict[str, Any]:
        expiry = time.time() + ttl_s if ttl_s else None
        self._store[key] = (value, expiry)
        logger.debug(f"InMemoryProvider: stored key={key}, ttl_s={ttl_s}")
        return {"key": key, "stored": True, "ttl_s": ttl_s}

    def get(self, key: str) -> dict[str, Any]:
        if key not in self._store:
            return {"key": key, "found": False}

        value, expiry = self._store[key]

        # Check TTL expiration
        if expiry and time.time() > expiry:
            del self._store[key]
            return {"key": key, "found": False}

        return {"key": key, "value": value, "found": True}

    def delete(self, key: str) -> dict[str, Any]:
        if key in self._store:
            del self._store[key]
            return {"key": key, "deleted": True}
        return {"key": key, "deleted": False}


# ============================================================
# SQLite Provider
# ============================================================


class SQLiteProvider(MemoryProvider):
    """
    SQLite-backed storage for persistent memory.

    Stores data in a local SQLite database file. Survives process restarts.
    Configure with: SQLITE_MEMORY_PATH (default: ~/.toolweaver/memory.db)
    """

    def __init__(self) -> None:
        db_path = os.getenv("SQLITE_MEMORY_PATH", str(Path.home() / ".toolweaver" / "memory.db"))
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expiry REAL
            )
        """)
        conn.commit()
        conn.close()

    def put(self, key: str, value: Any, ttl_s: int | None) -> dict[str, Any]:
        expiry = time.time() + ttl_s if ttl_s else None
        value_json = json.dumps(value)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO memory (key, value, expiry) VALUES (?, ?, ?)",
            (key, value_json, expiry),
        )
        conn.commit()
        conn.close()

        logger.debug(f"SQLiteProvider: stored key={key}, ttl_s={ttl_s}")
        return {"key": key, "stored": True, "ttl_s": ttl_s}

    def get(self, key: str) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT value, expiry FROM memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"key": key, "found": False}

        value_json, expiry = row

        # Check TTL expiration
        if expiry and time.time() > expiry:
            self.delete(key)
            return {"key": key, "found": False}

        value = json.loads(value_json)
        return {"key": key, "value": value, "found": True}

    def delete(self, key: str) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return {"key": key, "deleted": deleted}


# ============================================================
# Redis Provider
# ============================================================


class RedisProvider(MemoryProvider):
    """
    Redis-backed storage for distributed/shared memory.

    Stores data in Redis for multi-instance or persistent storage.
    Requires: pip install redis
    Configure with: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB
    """

    def __init__(self) -> None:
        try:
            import redis
        except ImportError as e:
            raise ValueError(
                "RedisProvider requires the 'redis' package. "
                "Install with: pip install redis"
            ) from e

        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )

    def put(self, key: str, value: Any, ttl_s: int | None) -> dict[str, Any]:
        value_json = json.dumps(value)

        if ttl_s:
            self.client.setex(key, ttl_s, value_json)
        else:
            self.client.set(key, value_json)

        logger.debug(f"RedisProvider: stored key={key}, ttl_s={ttl_s}")
        return {"key": key, "stored": True, "ttl_s": ttl_s}

    def get(self, key: str) -> dict[str, Any]:
        value_json = self.client.get(key)

        if value_json is None:
            return {"key": key, "found": False}
        # Redis type stubs may not be complete, assume sync client returns str | bytes
        value_text = cast("str | bytes", value_json)
        value = json.loads(value_text)
        return {"key": key, "value": value, "found": True}

    def delete(self, key: str) -> dict[str, Any]:
        result = self.client.delete(key)
        # Redis type stubs may not be complete, assume sync client returns int
        deleted = cast(int, result) > 0
        return {"key": key, "deleted": deleted}


# ============================================================
# PostgreSQL Provider
# ============================================================


class PostgreSQLProvider(MemoryProvider):
    """
    PostgreSQL-backed storage for enterprise-grade persistent memory.

    Stores data in PostgreSQL for ACID compliance and advanced querying.
    Requires: pip install psycopg2-binary
    Configure with: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    """

    def __init__(self) -> None:
        try:
            import psycopg2 as _pg  # noqa: F401
            self._psycopg2 = _pg
        except ImportError as e:
            raise ValueError(
                "PostgreSQLProvider requires the 'psycopg2-binary' package. "
                "Install with: pip install psycopg2-binary"
            ) from e

        self.conn_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "toolweaver"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }

        self._init_db()

    def _init_db(self) -> None:
        """Initialize the PostgreSQL database schema."""
        conn = self._psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL,
                expiry TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def put(self, key: str, value: Any, ttl_s: int | None) -> dict[str, Any]:
        from psycopg2.extras import Json

        # Calculate expiry timestamp
        expiry = None
        if ttl_s:
            import datetime
            expiry = datetime.datetime.now() + datetime.timedelta(seconds=ttl_s)

        conn = self._psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memory (key, value, expiry) VALUES (%s, %s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, expiry = EXCLUDED.expiry",
            (key, Json(value), expiry),
        )
        conn.commit()
        cursor.close()
        conn.close()

        logger.debug(f"PostgreSQLProvider: stored key={key}, ttl_s={ttl_s}")
        return {"key": key, "stored": True, "ttl_s": ttl_s}

    def get(self, key: str) -> dict[str, Any]:
        conn = self._psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value, expiry FROM memory WHERE key = %s AND (expiry IS NULL OR expiry > NOW())",
            (key,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return {"key": key, "found": False}

        value, _ = row
        return {"key": key, "value": value, "found": True}

    def delete(self, key: str) -> dict[str, Any]:

        conn = self._psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory WHERE key = %s", (key,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()

        return {"key": key, "deleted": deleted}


# ============================================================
# Provider Registry
# ============================================================


def register_memory_provider(name: str, provider_class: type[MemoryProvider]) -> None:
    """
    Register a custom memory provider.

    Args:
        name: Provider name (e.g., "redis", "sqlite", "custom")
        provider_class: Provider class (subclass of MemoryProvider)

    Example:
        register_memory_provider("redis", RedisProvider)
    """
    _MEMORY_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered memory provider: {name}")


def get_memory_provider(name: str) -> MemoryProvider | ProviderRouter[MemoryProvider]:
    """
    Get a memory provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "redis,sqlite,memory")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (e.g., "memory", "redis", "sqlite", "postgres") or comma-separated list

    Returns:
        MemoryProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or instantiation fails

    Examples:
        # Single provider
        provider = get_memory_provider("redis")
        provider.put("key", {"data": "value"}, ttl_s=300)

        # Automatic fallback chain
        provider = get_memory_provider("redis,sqlite,memory")
        # Tries redis first, falls back to sqlite, then inmemory
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for memory: {provider_names}")
        return ProviderRouter(
            provider_getter=get_memory_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    # Register built-in providers on first access
    if not _MEMORY_PROVIDERS:
        register_memory_provider("memory", InMemoryProvider)
        register_memory_provider("inmemory", InMemoryProvider)
        register_memory_provider("sqlite", SQLiteProvider)
        register_memory_provider("redis", RedisProvider)
        register_memory_provider("postgres", PostgreSQLProvider)
        register_memory_provider("postgresql", PostgreSQLProvider)

    if name not in _MEMORY_PROVIDERS:
        available = ", ".join(sorted(_MEMORY_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown memory provider: {name}. "
            f"Available: {available}. "
            f"Register custom providers with register_memory_provider()."
        )

    try:
        return _MEMORY_PROVIDERS[name]()
    except Exception as e:
        raise ValueError(f"Failed to initialize memory provider '{name}': {e}") from e


# Default instance for backward compatibility
_default_provider = InMemoryProvider()
