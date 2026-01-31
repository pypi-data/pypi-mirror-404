"""
SkillState: Redis-based state management for skills.

Provides persistent state storage for skill execution context, caching, and
state synchronization across skill instances.
"""

import hashlib
import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, cast

redis: Any | None = None
NoBackoff: type[Any] | None = None
Retry: type[Any] | None = None

try:
    import redis as _redis
    from redis.backoff import NoBackoff as _NoBackoff
    from redis.retry import Retry as _Retry
except ImportError:
    REDIS_AVAILABLE = False
else:
    redis = _redis
    NoBackoff = _NoBackoff
    Retry = _Retry
    REDIS_AVAILABLE = True

logger = logging.getLogger(__name__)


class SkillState:
    """Redis-based state manager for skill execution context and caching."""

    # Redis key prefixes
    PREFIX_STATE = "skill:state"
    PREFIX_CACHE = "skill:cache"
    PREFIX_METRICS = "skill:metrics"
    PREFIX_LOCKS = "skill:lock"
    PREFIX_SESSION = "skill:session"

    host: str
    port: int
    db: int
    default_ttl: int
    redis_client: Any | None

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 0,
        password: str | None = None,
        default_ttl: int = 3600,
        connect_timeout: float = 0.5,
    ):
        """
        Initialize SkillState with Redis connection.

        Reads from environment variables if host/port not provided:
        - REDIS_URL: Full Redis URL (takes precedence)
        - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD: Individual config

        Args:
            host: Redis host (defaults to env or localhost)
            port: Redis port (defaults to env or 6379)
            db: Redis database number
            password: Redis password (defaults to env)
            default_ttl: Default time-to-live in seconds (1 hour)
            connect_timeout: Socket connect timeout in seconds
        """
        # Try to read from REDIS_URL first (SaaS format) only when host/port not explicitly provided
        if not REDIS_AVAILABLE:
            logger.warning("Redis is not installed. SkillState persistence will be disabled.")
            self.redis_client = None
            self.default_ttl = default_ttl
            self.host = "localhost" # Dummy
            self.port = 6379
            self.db = 0
            return

        redis_url = os.getenv("REDIS_URL")
        redis_password = os.getenv("REDIS_PASSWORD")

        # Initialize host with default to ensure type consistency
        self.host = host if host is not None else (os.getenv("REDIS_HOST") or "localhost")

        if redis_url and host is None and port is None:
            try:
                # Don't pass db when using URL (Cloud plans don't support multiple DBs)
                retry_obj = cast(Any, Retry)(cast(Any, NoBackoff)(), 1) if Retry and NoBackoff else None
                self.redis_client = cast(Any, redis).from_url(
                    redis_url,
                    password=redis_password,  # Explicitly pass password if URL doesn't include it
                    decode_responses=True,
                    socket_connect_timeout=connect_timeout,
                    socket_timeout=connect_timeout,
                    retry=retry_obj,
                )
                self.redis_client.ping()
                logger.info("Connected to Redis via REDIS_URL for state management")
                # Preserve metadata for tests and diagnostics (don't reassign host since it's str typed)
                self.port = int(os.getenv("REDIS_PORT", "6379"))
                self.db = 0  # Store for reference, but URL takes precedence
                self.default_ttl = default_ttl
                return
            except Exception as e:
                logger.warning(f"Failed to connect via REDIS_URL: {e}; trying host/port config")

        # Fall back to host/port/password config from env or defaults
        host_val = self.host  # Already initialized above
        port_val = port or int(os.getenv("REDIS_PORT", "6379"))
        password = password or os.getenv("REDIS_PASSWORD")

        self.port = port_val
        self.db = db
        self.default_ttl = default_ttl

        try:
            if not redis:
                raise ImportError("redis package not installed")
            retry_obj = cast(Any, Retry)(cast(Any, NoBackoff)(), 1) if Retry and NoBackoff else None
            self.redis_client = cast(Any, redis).Redis(
                host=host_val,
                port=port_val,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=connect_timeout,
                socket_timeout=connect_timeout,
                retry=retry_obj,  # fail fast
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}/{db}")
        except Exception as e:
            if redis and isinstance(e, cast(Any, redis).ConnectionError):
                logger.error(f"Failed to connect to Redis: {e}")
            else:
                logger.error(f"Failed to connect to Redis: {e}")
            raise

    @staticmethod
    def _encode(value: Any) -> str:
        """Encode value as JSON."""
        return json.dumps(value)

    @staticmethod
    def _decode(value: str | None) -> Any:
        """Decode JSON value."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    # ===== State Management =====

    def set_state(
        self,
        skill_name: str,
        state_key: str,
        value: Any,
        ttl: int | None = None,
        context: str | None = None,
    ) -> None:
        """
        Set skill state value with optional TTL.

        Args:
            skill_name: Name of the skill
            state_key: State key within the skill
            value: Value to store (serialized to JSON)
            ttl: Time-to-live in seconds (uses default if None)
            context: Optional context/namespace for state isolation
        """
        key = self._build_key(skill_name, state_key, context, self.PREFIX_STATE)
        ttl = ttl or self.default_ttl

        if not self.redis_client:
            logger.debug(f"Skipping set_state for {key}: Redis not available")
            return

        self.redis_client.setex(
            key,
            ttl,
            self._encode(value),
        )
        logger.debug(f"Set state {key} with TTL {ttl}s")

    def get_state(
        self,
        skill_name: str,
        state_key: str,
        context: str | None = None,
        default: Any = None,
    ) -> Any:
        """
        Get skill state value.

        Args:
            skill_name: Name of the skill
            state_key: State key within the skill
            context: Optional context/namespace
            default: Default value if not found

        Returns:
            State value or default
        """
        key = self._build_key(skill_name, state_key, context, self.PREFIX_STATE)

        if not self.redis_client:
            logger.debug(f"Skipping get_state for {key}: Redis not available")
            return default

        value = self.redis_client.get(key)


        if value is None:
            return default

        return self._decode(value)

    def delete_state(
        self,
        skill_name: str,
        state_key: str,
        context: str | None = None,
    ) -> bool:
        """
        Delete skill state.

        Args:
            skill_name: Name of the skill
            state_key: State key to delete
            context: Optional context/namespace

        Returns:
            True if deleted, False if not found
        """
        if not self.redis_client:
            logger.debug("Skipping delete_state: Redis not available")
            return False

        key = self._build_key(skill_name, state_key, context, self.PREFIX_STATE)
        return bool(self.redis_client.delete(key))

    def get_all_state(
        self,
        skill_name: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all state for a skill.

        Args:
            skill_name: Name of the skill
            context: Optional context/namespace

        Returns:
            Dictionary of all state keys/values
        """
        if not self.redis_client:
            logger.debug("Skipping get_all_state: Redis not available")
            return {}

        pattern = self._build_key(skill_name, "*", context, self.PREFIX_STATE)
        keys = self.redis_client.keys(pattern)

        result = {}
        for key in keys:
            state_key = key.split(":")[-1]
            result[state_key] = self._decode(self.redis_client.get(key))

        return result

    def get_skill_state(self, skill_name: str, context: str | None = None) -> dict[str, Any]:
        """
        Get all state for a skill (API convenience alias).

        Args:
            skill_name: Name of the skill
            context: Optional context/namespace

        Returns:
            Dictionary of all state keys/values
        """
        try:
            return self.get_all_state(skill_name, context)
        except Exception as e:
            logger.warning(f"Failed to get state for {skill_name}: {e}")
            return {}

    def clear_state(
        self,
        skill_name: str,
        context: str | None = None,
    ) -> int:
        """
        Clear all state for a skill.

        Args:
            skill_name: Name of the skill
            context: Optional context/namespace

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            logger.debug("Skipping clear_state: Redis not available")
            return 0

        pattern = self._build_key(skill_name, "*", context, self.PREFIX_STATE)
        keys = self.redis_client.keys(pattern)

        if keys:
            return self.redis_client.delete(*keys)
        return 0

    # ===== Cache Operations =====

    def set_cache(
        self,
        skill_name: str,
        cache_key: str,
        value: Any,
        ttl: int | None = None,
        context: str | None = None,
    ) -> None:
        """
        Set cache value.

        Args:
            skill_name: Name of the skill
            cache_key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            context: Optional context/namespace
        """
        if not self.redis_client:
            logger.debug("Skipping set_cache: Redis not available")
            return

        key = self._build_key(skill_name, cache_key, context, self.PREFIX_CACHE)
        ttl = ttl or self.default_ttl

        self.redis_client.setex(
            key,
            ttl,
            self._encode(value),
        )

    def get_cache(
        self,
        skill_name: str,
        cache_key: str,
        context: str | None = None,
    ) -> Any | None:
        """
        Get cached value.

        Args:
            skill_name: Name of the skill
            cache_key: Cache key
            context: Optional context/namespace

        Returns:
            Cached value or None
        """
        key = self._build_key(skill_name, cache_key, context, self.PREFIX_CACHE)

        if not self.redis_client:
            logger.debug("Skipping get_cache: Redis not available")
            return None

        value = self.redis_client.get(key)
        return self._decode(value) if value else None

    def invalidate_cache(
        self,
        skill_name: str,
        pattern: str | None = None,
        context: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            skill_name: Name of the skill
            pattern: Optional glob pattern (e.g., "request:*")
            context: Optional context/namespace

        Returns:
            Number of keys invalidated
        """
        search_pattern = pattern or "*"
        key_pattern = self._build_key(skill_name, search_pattern, context, self.PREFIX_CACHE)

        if not self.redis_client:
            logger.debug("Skipping invalidate_cache: Redis not available")
            return 0

        keys = self.redis_client.keys(key_pattern)

        if keys:
            return self.redis_client.delete(*keys)
        return 0

    # ===== Distributed Locking =====

    @contextmanager
    def lock(
        self,
        lock_name: str,
        timeout: int = 30,
        blocking: bool = True,
    ) -> Iterator[Any]:
        """
        Context manager for distributed locks.

        Args:
            lock_name: Name of the lock
            timeout: Lock timeout in seconds
            blocking: Whether to block until lock is acquired

        Yields:
            Lock ID (nonce)

        Example:
            with skill_state.lock("critical_section"):
                # Perform critical operation
                pass
        """
        key = f"{self.PREFIX_LOCKS}:{lock_name}"
        lock_id = hashlib.md5(f"{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()

        if not self.redis_client:
            logger.debug(f"Returning dummy lock for {lock_name}: Redis not available")
            yield "offline_dummy_lock"
            return

        # Try to acquire lock
        acquired = False
        if blocking:
            # Block until lock acquired
            start_time = datetime.now(timezone.utc)
            while not acquired:
                if self.redis_client.set(key, lock_id, nx=True, ex=timeout):
                    acquired = True
                    break
                if (datetime.now(timezone.utc) - start_time).seconds > timeout:
                    raise TimeoutError(f"Failed to acquire lock {lock_name}")
                # Sleep briefly to avoid busy waiting
                import time

                time.sleep(0.01)
        else:
            # Non-blocking attempt
            acquired = bool(self.redis_client.set(key, lock_id, nx=True, ex=timeout))

        if not acquired:
            raise RuntimeError(f"Could not acquire lock {lock_name}")

        try:
            yield lock_id
        finally:
            # Release lock only if we still own it
            current = self.redis_client.get(key)
            if current == lock_id:
                self.redis_client.delete(key)
                logger.debug(f"Released lock {lock_name}")

    # ===== Session Management =====

    def create_session(
        self,
        skill_name: str,
        session_id: str,
        data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """
        Create a skill execution session.

        Args:
            skill_name: Name of the skill
            session_id: Unique session ID
            data: Session data
            ttl: Session TTL in seconds
        """
        if not self.redis_client:
            logger.debug(f"Skipping create_session {session_id}: Redis not available")
            return

        key = f"{self.PREFIX_SESSION}:{skill_name}:{session_id}"
        ttl = ttl or self.default_ttl

        self.redis_client.setex(
            key,
            ttl,
            self._encode(
                {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    **data,
                }
            ),
        )
        logger.debug(f"Created session {session_id} for {skill_name}")

    def get_session(
        self,
        skill_name: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        """
        Get session data.

        Args:
            skill_name: Name of the skill
            session_id: Session ID

        Returns:
            Session data or None
        """
        if not self.redis_client:
            logger.debug(f"Skipping get_session {session_id}: Redis not available")
            return None

        key = f"{self.PREFIX_SESSION}:{skill_name}:{session_id}"
        value = self.redis_client.get(key)
        return self._decode(value) if value else None

    def delete_session(
        self,
        skill_name: str,
        session_id: str,
    ) -> bool:
        """
        Delete a session.

        Args:
            skill_name: Name of the skill
            session_id: Session ID

        Returns:
            True if deleted
        """
        if not self.redis_client:
            logger.debug(f"Skipping delete_session {session_id}: Redis not available")
            return False

        key = f"{self.PREFIX_SESSION}:{skill_name}:{session_id}"
        return bool(self.redis_client.delete(key))

    def list_sessions(
        self,
        skill_name: str,
    ) -> list[str]:
        """
        List all sessions for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of session IDs
        """
        if not self.redis_client:
            logger.debug("Skipping list_sessions: Redis not available")
            return []

        pattern = f"{self.PREFIX_SESSION}:{skill_name}:*"
        keys = self.redis_client.keys(pattern)
        return [key.split(":")[-1] for key in keys]

    # ===== Utility Methods =====

    @staticmethod
    def _build_key(
        skill_name: str,
        key: str,
        context: str | None,
        prefix: str,
    ) -> str:
        """Build a Redis key with prefix, skill, context."""
        if context:
            return f"{prefix}:{skill_name}:{context}:{key}"
        return f"{prefix}:{skill_name}:{key}"

    def expire(self, key: str, ttl: int) -> None:
        """Set expiration on a key."""
        if self.redis_client:
            self.redis_client.expire(key, ttl)

    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key (-1 = no expiry, -2 = not exists)."""
        if not self.redis_client:
            return -2
        return self.redis_client.ttl(key)

    def flush_all(self) -> None:
        """⚠️ Clear all skill data from Redis."""
        if not self.redis_client:
            logger.debug("Skipping flush_all: Redis not available")
            return

        pattern = f"{self.PREFIX_STATE}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

        logger.warning("Flushed all skill state from Redis")

    def health_check(self) -> dict[str, Any]:
        """
        Get Redis connection health.

        Returns:
            Health status dictionary
        """
        if not self.redis_client:
            return {
                "status": "disabled",
                "connected": False,
                "reason": "Redis not available"
            }

        try:
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": info.get("connected_clients"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }
