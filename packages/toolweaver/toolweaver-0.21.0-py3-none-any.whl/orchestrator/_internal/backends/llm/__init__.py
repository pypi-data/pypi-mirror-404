"""LLM Provider Implementations

Abstract: LLMProvider (base.py)
Implementations:
- LiteLLMProvider - LiteLLM-based provider (OpenAI, Claude, etc.)

Phase 1+: Direct provider implementations, local models
"""

from orchestrator._internal.backends.llm.base import LLMProvider
from orchestrator._internal.backends.llm.litellm import LiteLLMProvider

__all__ = ["LLMProvider", "LiteLLMProvider"]
