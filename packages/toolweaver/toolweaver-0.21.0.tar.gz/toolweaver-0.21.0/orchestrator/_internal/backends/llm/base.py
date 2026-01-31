"""
LLM Provider - Abstract Base Class

Defines the interface for interacting with language models.
Supports multiple providers via pluggable architecture.

Phase 0: LiteLLM wrapper (current)
Phase 1: Direct API providers
Phase 3: Local model providers
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when LLM operations fail."""

    pass


class LLMProvider(ABC):
    """
    Abstract base class for LLM provider strategies.

    Providers handle communication with language models.
    Different implementations support LiteLLM, direct APIs, or local models.

    Example:
        provider = get_llm_provider("litellm")
        response = provider.complete("Hello, world!")
        print(response)
    """

    @abstractmethod
    def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """
        Generate completion for a prompt.

        Args:
            prompt: Input text/prompt
            model: Model identifier (provider-specific)
            **kwargs: Model parameters (temperature, max_tokens, etc.)

        Returns:
            Completion text

        Raises:
            LLMError: If completion fails
        """
        pass

    @abstractmethod
    def stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> Iterator[str]:
        """
        Stream completion chunks for a prompt.

        Args:
            prompt: Input text/prompt
            model: Model identifier
            **kwargs: Model parameters

        Yields:
            Completion text chunks

        Raises:
            LLMError: If streaming fails
        """
        pass

    @abstractmethod
    def get_models(self, **kwargs: Any) -> list[str]:
        """
        List available models.

        Args:
            **kwargs: Provider-specific filters

        Returns:
            List of model identifiers
        """
        pass

    @abstractmethod
    def validate_model(self, model: str, **kwargs: Any) -> bool:
        """
        Check if model is available/valid.

        Args:
            model: Model identifier
            **kwargs: Provider-specific options

        Returns:
            True if model is available
        """
        pass


def get_llm_provider(provider_type: str = "litellm", **kwargs: Any) -> LLMProvider:
    """
    Factory function to get LLM provider instance.

    Args:
        provider_type: Type of provider ("litellm", "openai", "anthropic", "local")
        **kwargs: Provider-specific initialization parameters

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider_type is unknown
        LLMError: If initialization fails

    Example:
        # LiteLLM provider (default)
        provider = get_llm_provider("litellm")

        # Direct OpenAI (Phase 1)
        provider = get_llm_provider("openai", api_key="sk-...")

        # Local model (Phase 3)
        provider = get_llm_provider("local", model_path="./models/llama2")
    """
    from .litellm import LiteLLMProvider

    providers = {
        "litellm": LiteLLMProvider,
    }

    # Phase 1: Add direct providers
    # try:
    #     from .openai import OpenAIProvider
    #     providers["openai"] = OpenAIProvider
    # except ImportError:
    #     pass

    # try:
    #     from .anthropic import AnthropicProvider
    #     providers["anthropic"] = AnthropicProvider
    # except ImportError:
    #     pass

    # Phase 3: Add local providers
    # try:
    #     from .local import LocalLLMProvider
    #     providers["local"] = LocalLLMProvider
    # except ImportError:
    #     pass

    provider_class = providers.get(provider_type)
    if not provider_class:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown provider type: {provider_type}. Available providers: {available}"
        )

    try:
        return provider_class(**kwargs)
    except Exception as e:
        raise LLMError(f"Failed to initialize {provider_type} provider: {e}") from e
