"""
LiteLLM Provider

Wrapper for LiteLLM library - provides unified interface to 100+ LLM providers.
Current default implementation.
"""

import logging
from collections.abc import Iterator
from typing import Any, cast

from .base import LLMError, LLMProvider

logger = logging.getLogger(__name__)


class LiteLLMProvider(LLMProvider):
    """
    LiteLLM-based provider for multi-model support.

    Supports OpenAI, Anthropic, Google, Azure, AWS, and 100+ providers
    through unified interface.

    Example:
        provider = LiteLLMProvider()

        # OpenAI
        response = provider.complete("Hello", model="gpt-4")

        # Anthropic
        response = provider.complete("Hello", model="claude-3-opus")

        # Streaming
        for chunk in provider.stream("Hello", model="gpt-4"):
            print(chunk, end="")
    """

    def __init__(self, default_model: str | None = None) -> None:
        """
        Initialize LiteLLM provider.

        Args:
            default_model: Default model to use if not specified
        """
        try:
            import litellm

            self.litellm = litellm
        except ImportError:
            raise LLMError(
                "litellm package not installed. Install with: pip install litellm"
            ) from None

        self.default_model = default_model or "gpt-3.5-turbo"
        logger.info(f"Initialized LiteLLMProvider with default: {self.default_model}")

    def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate completion using LiteLLM."""
        try:
            model = model or self.default_model
            response = self.litellm.completion(
                model=model, messages=[{"role": "user", "content": prompt}], **kwargs
            )
            content = response.choices[0].message.content
            return cast(str, content)

        except Exception as e:
            raise LLMError(f"Completion failed: {e}") from None

    def stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> Iterator[str]:
        """Stream completion chunks using LiteLLM."""
        try:
            model = model or self.default_model
            response = self.litellm.completion(
                model=model, messages=[{"role": "user", "content": prompt}], stream=True, **kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMError(f"Streaming failed: {e}") from None

    def get_models(self, **kwargs: Any) -> list[str]:
        """
        List available models (common ones).

        Note: LiteLLM supports 100+ models, returning subset.
        """
        return [
            # OpenAI
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            # Anthropic
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            # Google
            "gemini-pro",
            # Open source
            "ollama/llama2",
            "ollama/mistral",
        ]

    def validate_model(self, model: str, **kwargs: Any) -> bool:
        """Check if model identifier looks valid."""
        # Basic validation - check if it's a non-empty string
        # LiteLLM will validate properly at runtime
        return bool(model and isinstance(model, str))

    def __repr__(self) -> str:
        return f"LiteLLMProvider(default={self.default_model})"
