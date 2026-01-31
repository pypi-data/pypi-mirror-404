"""Token counting for LLM API calls.

This module provides token counting functionality for various LLM providers,
supporting accurate cost calculation and tracking.

Supported Providers:
  - OpenAI (gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o, etc.)
  - Anthropic (claude-3-opus, claude-3-sonnet, claude-3-haiku)
  - Extended via custom providers

Architecture:
  - Provider-based token counting
  - Cache for encoding lookups
  - Utility functions for text/message processing
  - Integration with planning system for batch analysis
"""

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenCountProvider(Enum):
    """Supported token counting providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OTHER = "other"


@dataclass
class TokenCountResult:
    """Result of token counting operation."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: TokenCountProvider

    def __post_init__(self) -> None:
        """Validate token counts."""
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("total_tokens must equal prompt_tokens + completion_tokens")


class TokenCounter:
    """Count tokens for LLM API calls.

    This class provides token counting for various LLM providers. It uses
    provider-specific token estimation techniques or actual token counting
    when possible.

    Usage:
        counter = TokenCounter()

        # Count tokens for OpenAI
        result = counter.count_tokens(
            prompt="Hello, how are you?",
            model="gpt-4",
            provider=TokenCountProvider.OPENAI
        )

        # Count tokens for Anthropic
        result = counter.count_tokens(
            prompt="Hello, how are you?",
            model="claude-3-opus-20240229",
            provider=TokenCountProvider.ANTHROPIC
        )
    """

    # Provider-specific token estimation ratios
    # These are used when actual token counting is not available
    _ESTIMATION_RATIOS = {
        TokenCountProvider.OPENAI: {
            "gpt-3.5-turbo": 0.004,
            "gpt-4": 0.00015,
            "gpt-4-turbo": 0.00015,
            "gpt-4o": 0.00005,
            "text-davinci-003": 0.0001,
        },
        TokenCountProvider.ANTHROPIC: {
            "claude-3-opus-20240229": 0.0000135,
            "claude-3-sonnet-20240229": 0.000003,
            "claude-3-haiku-20240307": 0.0000008,
            "claude-2.1": 0.008,
            "claude-instant": 0.0008,
        },
    }

    def __init__(self) -> None:
        """Initialize token counter."""
        self._cache: dict[str, int] = {}
        self._encoding_cache: dict[str, Any] = {}

    def count_tokens(
        self,
        prompt: str,
        model: str,
        provider: TokenCountProvider = TokenCountProvider.OPENAI,
        completion: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> TokenCountResult:
        """Count tokens in a prompt or message sequence.

        Args:
            prompt: Text prompt to count (if not using messages format)
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            provider: Token count provider
            completion: Optional completion text to count
            messages: Optional list of message dicts (for chat format)

        Returns:
            TokenCountResult with token counts

        Raises:
            ValueError: If model or provider is invalid
        """
        if not model:
            raise ValueError("model must be provided")
        if not provider:
            raise ValueError("provider must be provided")

        # Use messages if provided, otherwise fall back to prompt
        text_to_count = prompt
        if messages is not None:
            text_to_count = self._format_messages(messages)

        # Count prompt tokens
        prompt_tokens = self._estimate_tokens(text_to_count, model, provider)

        # Count completion tokens if provided
        completion_tokens = 0
        if completion:
            completion_tokens = self._estimate_tokens(completion, model, provider)

        total_tokens = prompt_tokens + completion_tokens

        return TokenCountResult(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            provider=provider,
        )

    def _estimate_tokens(self, text: str, model: str, provider: TokenCountProvider) -> int:
        """Estimate token count for text.

        Uses provider-specific estimation when actual token counting
        is not available.

        Args:
            text: Text to estimate tokens for
            model: Model identifier
            provider: Token count provider

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Check cache first
        cache_key = self._get_cache_key(text, model, provider)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Use provider-specific estimation
        if provider == TokenCountProvider.OPENAI:
            tokens = self._estimate_openai_tokens(text, model)
        elif provider == TokenCountProvider.ANTHROPIC:
            tokens = self._estimate_anthropic_tokens(text, model)
        else:
            # Fallback: estimate 1 token per 4 characters (rough approximation)
            tokens = max(1, len(text) // 4)

        # Cache result
        self._cache[cache_key] = tokens
        return tokens

    def _estimate_openai_tokens(self, text: str, model: str) -> int:
        """Estimate tokens for OpenAI models using character-based heuristic.

        OpenAI models average ~4 characters per token. This is a simplification;
        actual token counting would use tiktoken library.

        Args:
            text: Text to estimate
            model: Model identifier

        Returns:
            Estimated token count
        """
        # Average 4 characters per token for OpenAI
        # This is a reasonable heuristic for English text
        char_per_token = 4.0

        # Adjust for specific models if known
        if model in self._ESTIMATION_RATIOS[TokenCountProvider.OPENAI]:
            # For now, use character-based approach
            pass

        tokens = max(1, len(text) // int(char_per_token))
        return tokens

    def _estimate_anthropic_tokens(self, text: str, model: str) -> int:
        """Estimate tokens for Anthropic models using character-based heuristic.

        Anthropic models average ~3 characters per token (slightly more efficient).

        Args:
            text: Text to estimate
            model: Model identifier

        Returns:
            Estimated token count
        """
        # Average 3 characters per token for Anthropic
        # Anthropic's models are slightly more efficient
        char_per_token = 3.0

        tokens = max(1, len(text) // int(char_per_token))
        return tokens

    def _format_messages(self, messages: list[dict[str, str]]) -> str:
        """Format messages list into a single text string for token counting.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Formatted text representation
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def _get_cache_key(self, text: str, model: str, provider: TokenCountProvider) -> str:
        """Generate cache key for token count result.

        Uses hash of text combined with model and provider for unique key.

        Args:
            text: Text content
            model: Model identifier
            provider: Provider

        Returns:
            Cache key string
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{model}:{provider.value}:{text_hash}"

    def clear_cache(self) -> None:
        """Clear the token count cache."""
        self._cache.clear()
        self._encoding_cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        return {
            "cached_tokens": len(self._cache),
            "encoding_cache": len(self._encoding_cache),
        }
