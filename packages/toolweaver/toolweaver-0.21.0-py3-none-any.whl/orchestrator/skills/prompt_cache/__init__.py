"""
Prompt Cache Skill

Thin wrapper around orchestrator._internal.cost.prompt_cache
following the Agent Skills specification.
"""

from typing import Any, Optional

from orchestrator._internal.cost.prompt_cache import PromptCache

# Global cache instance
_cache = None


def get_cache() -> PromptCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = PromptCache()
    return _cache


def cache_prompt(
    prompt: str,
    model: str,
    provider: str,
    response: str,
    cost_cents: float = 0.0,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    """Cache a prompt result for similarity matching."""
    cache = get_cache()
    cached = cache.add(
        prompt=prompt,
        model=model,
        provider=provider,
        response=response,
        cost_cents=cost_cents,
        ttl_seconds=ttl_seconds,
    )

    return {
        "prompt": cached.prompt,
        "model": cached.model,
        "provider": cached.provider,
        "response": cached.response,
        "cached_at": cached.cached_at.isoformat(),
        "expires_at": cached.expires_at.isoformat(),
    }


def find_similar_prompt(
    prompt: str, model: str | None = None, provider: str | None = None, min_similarity: float = 0.8
) -> dict[str, Any] | None:
    """Find a similar cached prompt using similarity matching."""
    cache = get_cache()
    cached = cache.find_similar(prompt=prompt, model=model, provider=provider)

    if cached is None:
        return None

    return {
        "prompt": cached.prompt,
        "model": cached.model,
        "provider": cached.provider,
        "response": cached.response,
        "hit_count": cached.hit_count,
        "cached_at": cached.cached_at.isoformat(),
    }


def get_exact_prompt(
    prompt: str, model: str | None = None, provider: str | None = None
) -> dict[str, Any] | None:
    """Get an exact prompt match using hash lookup."""
    cache = get_cache()
    cached = cache.get_exact(prompt, model or "", provider or "")

    if cached is None:
        return None

    return {
        "prompt": cached.prompt,
        "model": cached.model,
        "provider": cached.provider,
        "response": cached.response,
        "hit_count": cached.hit_count,
        "cached_at": cached.cached_at.isoformat(),
    }


def cleanup_expired() -> int:
    """Remove expired prompt cache entries."""
    cache = get_cache()
    return cache.cleanup_expired()


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()


__all__ = [
    "cache_prompt",
    "find_similar_prompt",
    "get_exact_prompt",
    "cleanup_expired",
    "get_cache_stats",
]
