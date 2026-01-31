"""
Response Cache for LLM API Responses

Caches LLM responses to reduce redundant API calls and costs.
Supports TTL-based expiration, cache invalidation, and multi-provider responses.

Usage:
    from orchestrator._internal.cost.response_cache import ResponseCache

    cache = ResponseCache()

    # Check cache before API call
    cached = cache.get(prompt="What is 2+2?", model="gpt-4")
    if cached:
        return cached.response

    # Make API call and cache result
    response = llm_api_call(...)
    cache.set(prompt="What is 2+2?", model="gpt-4", response=response)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CachedResponse:
    """Cached LLM response with metadata."""

    prompt: str
    model: str
    provider: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    cost_cents: float
    cached_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt": self.prompt,
            "model": self.model,
            "provider": self.provider,
            "response": self.response,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_cents": self.cost_cents,
            "cached_at": self.cached_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedResponse":
        """Create from dictionary."""
        return cls(
            prompt=data["prompt"],
            model=data["model"],
            provider=data["provider"],
            response=data["response"],
            prompt_tokens=data["prompt_tokens"],
            completion_tokens=data["completion_tokens"],
            cost_cents=data["cost_cents"],
            cached_at=datetime.fromisoformat(data["cached_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            hit_count=data.get("hit_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if data.get("last_accessed")
            else None,
            metadata=data.get("metadata", {}),
        )

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > self.expires_at

    def record_hit(self) -> None:
        """Record cache hit."""
        self.hit_count += 1
        self.last_accessed = datetime.now()


class ResponseCache:
    """
    Cache for LLM API responses.

    Provides:
    - Response deduplication (same prompt + model = cached result)
    - TTL-based expiration
    - Cache hit/miss metrics
    - Invalidation strategies
    - Multi-provider support

    Cache key is hash of: prompt + model + provider + parameters
    """

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        """Initialize response cache.

        Args:
            default_ttl_seconds: Default TTL for cached responses (default: 1 hour)
        """
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: dict[str, CachedResponse] = {}

        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_savings_cents = 0.0

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        provider: str = "openai",
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate cache key from prompt and parameters.

        Args:
            prompt: LLM prompt
            model: Model identifier
            provider: Provider name
            parameters: Optional parameters (temperature, max_tokens, etc.)

        Returns:
            Cache key (hash)
        """
        # Normalize parameters
        params = parameters or {}

        # Create canonical string
        canonical = json.dumps(
            {
                "prompt": prompt.strip(),
                "model": model,
                "provider": provider,
                "parameters": dict(sorted(params.items())),
            },
            sort_keys=True,
        )

        # Generate hash
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        provider: str = "openai",
        parameters: dict[str, Any] | None = None,
    ) -> CachedResponse | None:
        """Get cached response if available.

        Args:
            prompt: LLM prompt
            model: Model identifier
            provider: Provider name
            parameters: Optional parameters

        Returns:
            CachedResponse if found and not expired, None otherwise
        """
        key = self._generate_cache_key(prompt, model, provider, parameters)

        if key not in self.cache:
            self.misses += 1
            return None

        cached = self.cache[key]

        # Check if expired
        if cached.is_expired():
            del self.cache[key]
            self.evictions += 1
            self.misses += 1
            return None

        # Record hit
        cached.record_hit()
        self.hits += 1
        self.total_savings_cents += cached.cost_cents

        return cached

    def set(
        self,
        prompt: str,
        model: str,
        provider: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_cents: float,
        ttl_seconds: int | None = None,
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CachedResponse:
        """Cache a response.

        Args:
            prompt: LLM prompt
            model: Model identifier
            provider: Provider name
            response: LLM response
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost_cents: Cost in cents
            ttl_seconds: TTL in seconds (default: use default_ttl_seconds)
            parameters: Optional parameters
            metadata: Optional metadata

        Returns:
            CachedResponse object
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

        now = datetime.now()
        cached = CachedResponse(
            prompt=prompt,
            model=model,
            provider=provider,
            response=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_cents=cost_cents,
            cached_at=now,
            expires_at=now + timedelta(seconds=ttl),
            metadata=metadata or {},
        )

        key = self._generate_cache_key(prompt, model, provider, parameters)
        self.cache[key] = cached

        return cached

    def invalidate(
        self, prompt: str | None = None, model: str | None = None, provider: str | None = None
    ) -> int:
        """Invalidate cache entries matching criteria.

        Args:
            prompt: Filter by prompt (optional)
            model: Filter by model (optional)
            provider: Filter by provider (optional)

        Returns:
            Number of entries invalidated
        """
        if prompt is None and model is None and provider is None:
            # Clear all
            count = len(self.cache)
            self.cache.clear()
            self.evictions += count
            return count

        # Filter and delete
        to_delete = []
        for key, cached in self.cache.items():
            match = True
            if prompt is not None and cached.prompt != prompt:
                match = False
            if model is not None and cached.model != model:
                match = False
            if provider is not None and cached.provider != provider:
                match = False

            if match:
                to_delete.append(key)

        for key in to_delete:
            del self.cache[key]

        self.evictions += len(to_delete)
        return len(to_delete)

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        to_delete = [key for key, cached in self.cache.items() if cached.is_expired()]

        for key in to_delete:
            del self.cache[key]

        self.evictions += len(to_delete)
        return len(to_delete)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "evictions": self.evictions,
            "total_savings_cents": self.total_savings_cents,
            "avg_hit_count": sum(c.hit_count for c in self.cache.values()) / len(self.cache)
            if self.cache
            else 0,
        }

    def get_top_cached(self, limit: int = 10) -> list[CachedResponse]:
        """Get most frequently accessed cached responses.

        Args:
            limit: Maximum number of results

        Returns:
            List of top cached responses sorted by hit count
        """
        sorted_cache = sorted(self.cache.values(), key=lambda c: c.hit_count, reverse=True)
        return sorted_cache[:limit]

    def get_cache_size_bytes(self) -> int:
        """Estimate cache size in bytes.

        Returns:
            Approximate size in bytes
        """
        size = 0
        for cached in self.cache.values():
            size += len(cached.prompt)
            size += len(cached.response)
            size += len(json.dumps(cached.metadata))
        return size

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        self.evictions += count


__all__ = ["ResponseCache", "CachedResponse"]
