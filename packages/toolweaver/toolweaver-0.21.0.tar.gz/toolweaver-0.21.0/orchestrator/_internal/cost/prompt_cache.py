"""
Prompt Cache for Similar Prompt Detection

Caches prompt results and matches similar prompts to reduce redundant API calls.
Uses similarity threshold to determine if a prompt is "close enough" to a cached one.

Usage:
    from orchestrator._internal.cost.prompt_cache import PromptCache

    cache = PromptCache(similarity_threshold=0.9)

    # Check for similar prompt
    similar = cache.find_similar("What is the capital of France?")
    if similar:
        return similar.response

    # Cache new prompt result
    cache.add(
        prompt="What is the capital of France?",
        response="Paris",
        model="gpt-4",
        cost_cents=0.03
    )
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CachedPrompt:
    """Cached prompt with response and metadata."""

    prompt: str
    response: str
    model: str
    provider: str
    cost_cents: float
    cached_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime | None = None
    prompt_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Generate prompt hash if not provided."""
        if not self.prompt_hash:
            self.prompt_hash = hashlib.md5(self.prompt.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > self.expires_at

    def record_hit(self) -> None:
        """Record cache hit."""
        self.hit_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "provider": self.provider,
            "cost_cents": self.cost_cents,
            "cached_at": self.cached_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "prompt_hash": self.prompt_hash,
            "metadata": self.metadata,
        }


class PromptCache:
    """
    Cache for prompt results with similarity matching.

    Provides:
    - Prompt result caching
    - Similarity-based matching (find prompts close to query)
    - TTL-based expiration
    - Hit/miss metrics

    Similarity is currently based on:
    - Exact match (similarity = 1.0)
    - Word overlap (simple Jaccard similarity)

    For production, consider using embeddings (sentence-transformers)
    for semantic similarity matching.
    """

    def __init__(self, similarity_threshold: float = 0.85, default_ttl_seconds: int = 7200):
        """Initialize prompt cache.

        Args:
            similarity_threshold: Minimum similarity score (0-1) for match
            default_ttl_seconds: Default TTL for cached prompts (default: 2 hours)
        """
        self.similarity_threshold = similarity_threshold
        self.default_ttl_seconds = default_ttl_seconds
        self.prompts: list[CachedPrompt] = []

        # Metrics
        self.hits = 0
        self.misses = 0
        self.total_savings_cents = 0.0

    def _calculate_similarity(self, prompt1: str, prompt2: str) -> float:
        """Calculate similarity between two prompts.

        Uses simple word-based Jaccard similarity.
        For production, use embeddings-based similarity.

        Args:
            prompt1: First prompt
            prompt2: Second prompt

        Returns:
            Similarity score (0-1)
        """
        # Normalize
        p1 = prompt1.lower().strip()
        p2 = prompt2.lower().strip()

        # Exact match
        if p1 == p2:
            return 1.0

        # Word-based Jaccard similarity
        words1 = set(p1.split())
        words2 = set(p2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def find_similar(
        self, prompt: str, model: str | None = None, provider: str | None = None
    ) -> CachedPrompt | None:
        """Find similar cached prompt.

        Args:
            prompt: Prompt to match
            model: Optional model filter
            provider: Optional provider filter

        Returns:
            CachedPrompt if similar prompt found, None otherwise
        """
        best_match = None
        best_similarity = 0.0

        for cached in self.prompts:
            # Skip expired
            if cached.is_expired():
                continue

            # Apply filters
            if model and cached.model != model:
                continue
            if provider and cached.provider != provider:
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(prompt, cached.prompt)

            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = cached

        if best_match:
            best_match.record_hit()
            self.hits += 1
            self.total_savings_cents += best_match.cost_cents
            return best_match
        else:
            self.misses += 1
            return None

    def add(
        self,
        prompt: str,
        response: str,
        model: str,
        provider: str,
        cost_cents: float,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CachedPrompt:
        """Add prompt result to cache.

        Args:
            prompt: Prompt text
            response: Response text
            model: Model identifier
            provider: Provider name
            cost_cents: Cost in cents
            ttl_seconds: TTL in seconds (default: use default_ttl_seconds)
            metadata: Optional metadata

        Returns:
            CachedPrompt object
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

        now = datetime.now()
        cached = CachedPrompt(
            prompt=prompt,
            response=response,
            model=model,
            provider=provider,
            cost_cents=cost_cents,
            cached_at=now,
            expires_at=now + timedelta(seconds=ttl),
            metadata=metadata or {},
        )

        self.prompts.append(cached)
        return cached

    def get_exact(self, prompt: str, model: str, provider: str) -> CachedPrompt | None:
        """Get exact match for prompt (no similarity threshold).

        Args:
            prompt: Exact prompt text
            model: Model identifier
            provider: Provider name

        Returns:
            CachedPrompt if exact match found, None otherwise
        """
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

        for cached in self.prompts:
            if (
                cached.prompt_hash == prompt_hash
                and cached.model == model
                and cached.provider == provider
                and not cached.is_expired()
            ):
                cached.record_hit()
                self.hits += 1
                self.total_savings_cents += cached.cost_cents
                return cached

        self.misses += 1
        return None

    def cleanup_expired(self) -> int:
        """Remove expired prompts.

        Returns:
            Number of prompts removed
        """
        before = len(self.prompts)
        self.prompts = [p for p in self.prompts if not p.is_expired()]
        return before - len(self.prompts)

    def clear(self) -> None:
        """Clear all cached prompts."""
        self.prompts.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self.prompts),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "total_savings_cents": self.total_savings_cents,
            "similarity_threshold": self.similarity_threshold,
            "avg_hit_count": sum(p.hit_count for p in self.prompts) / len(self.prompts)
            if self.prompts
            else 0,
        }

    def get_top_prompts(self, limit: int = 10) -> list[CachedPrompt]:
        """Get most frequently matched prompts.

        Args:
            limit: Maximum number of results

        Returns:
            List of top prompts sorted by hit count
        """
        sorted_prompts = sorted(self.prompts, key=lambda p: p.hit_count, reverse=True)
        return sorted_prompts[:limit]


__all__ = ["PromptCache", "CachedPrompt"]
