"""
LLM Provider Package (DEPRECATED - use _internal.backends.llm).

Provides pluggable LLM providers for language model interactions.

Re-exports from new location for backwards compatibility.
"""

from orchestrator._internal.backends.llm.base import LLMError, LLMProvider, get_llm_provider
from orchestrator._internal.backends.llm.litellm import LiteLLMProvider

__all__ = [
    "LLMProvider",
    "LLMError",
    "get_llm_provider",
    "LiteLLMProvider",
]
