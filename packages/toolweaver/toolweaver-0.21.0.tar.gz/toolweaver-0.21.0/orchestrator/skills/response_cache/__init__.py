"""
Response Cache Skill

Thin wrapper around orchestrator._internal.cost.response_cache
following the Agent Skills specification.
"""

from typing import Any, Optional

from orchestrator._internal.cost.response_cache import ResponseCache

# Global cache instance
_cache = None


def get_cache() -> ResponseCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache


def cache_response(
    prompt: str,
    model: str,
    provider: str,
    response: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_cents: float,
    ttl_seconds: int | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cache an LLM response for future reuse."""
    cache = get_cache()
    cached = cache.set(
        prompt=prompt,
        model=model,
        provider=provider,
        response=response,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_cents=cost_cents,
        ttl_seconds=ttl_seconds,
        parameters=parameters,
    )

    return {
        "prompt": cached.prompt,
        "model": cached.model,
        "provider": cached.provider,
        "response": cached.response,
        "cost_cents": cached.cost_cents,
        "cached_at": cached.cached_at.isoformat(),
        "expires_at": cached.expires_at.isoformat(),
    }


def get_cached_response(
    prompt: str, model: str, provider: str, parameters: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Retrieve a cached response if available."""
    cache = get_cache()
    cached = cache.get(prompt, model, provider, parameters)

    if cached is None:
        return None

    return {
        "prompt": cached.prompt,
        "model": cached.model,
        "provider": cached.provider,
        "response": cached.response,
        "cost_cents": cached.cost_cents,
        "hit_count": cached.hit_count,
        "cached_at": cached.cached_at.isoformat(),
    }


def invalidate_cache(
    prompt: str | None = None, model: str | None = None, provider: str | None = None
) -> int:
    """Invalidate cached responses."""
    cache = get_cache()

    if prompt and model and provider:
        # Invalidate specific entry
        count = cache.invalidate(prompt, model, provider)
    elif model:
        # Invalidate by model
        count = cache.invalidate_by_model(model)  # type: ignore[attr-defined]
    elif provider:
        # Would need to add this method to ResponseCache
        # For now, just return 0
        count = 0
    else:
        # Clear all
        count = len(cache.cache)
        cache.cache.clear()

    return count


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics and performance metrics."""
    cache = get_cache()
    return cache.get_stats()


def cleanup_expired() -> int:
    """Remove expired cache entries."""
    cache = get_cache()
    return cache.cleanup_expired()


__all__ = [
    "cache_response",
    "get_cached_response",
    "invalidate_cache",
    "get_cache_stats",
    "cleanup_expired",
]
