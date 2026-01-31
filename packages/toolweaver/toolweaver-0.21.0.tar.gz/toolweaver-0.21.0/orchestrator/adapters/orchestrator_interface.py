"""
Orchestrator Interface - Vendor-neutral planner abstraction

Defines:
- ToolCall: Structured tool invocation with parameters
- PlanResult: Planning result with tool calls and reasoning
- OrchestratorConfig: Configuration for planner backends
- OrchestratorBackend: Abstract base for planner implementations (Claude, OpenAI, Ollama, etc.)

Architecture:
    This interface decouples ToolWeaver execution from specific planning models.
    Implementations include:
    - ClaudeOrchestrator (Claude SDK)
    - OpenAIOrchestrator (OpenAI API)
    - OllamaOrchestrator (Ollama local)

    All backends support:
    - Tool schema registration
    - Streaming responses (optional)
    - Error recovery and retries
    - Conversation history
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ToolCall:
    """Structured tool call (LLM → ToolWeaver execution)."""

    tool_name: str
    """Name of tool to execute (must match ToolRegistry)."""

    parameters: dict[str, Any]
    """Input parameters for tool. Keys must match tool schema."""

    id: str | None = None
    """Unique ID for this tool call (for tracking results)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> ToolCall:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PlanResult:
    """Result from orchestrator planning (thinking → tool calls)."""

    reasoning: str
    """Planning reasoning or explanation."""

    tool_calls: list[ToolCall]
    """Ordered list of tool calls to execute."""

    stop_reason: str = "tool_use"
    """Why planning stopped (tool_use, end_turn, max_tokens, error)."""

    metadata: dict[str, Any] | None = None
    """Backend-specific metadata (tokens, latency, etc.)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reasoning": self.reasoning,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "stop_reason": self.stop_reason,
            "metadata": self.metadata or {},
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanResult:
        """Create from dictionary."""
        tool_calls = [ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])]
        return cls(
            reasoning=data["reasoning"],
            tool_calls=tool_calls,
            stop_reason=data.get("stop_reason", "tool_use"),
            metadata=data.get("metadata"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> PlanResult:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator backends."""

    # Model selection
    model: str = "claude-3-5-sonnet-20241022"
    """Model identifier (e.g., claude-3-5-sonnet, gpt-4, ollama/mistral)."""

    # API configuration
    api_key: str | None = None
    """API key for service (Claude, OpenAI, etc.). Auto-loaded from env if None."""

    base_url: str | None = None
    """Base URL for API (useful for local Ollama, LiteLLM proxy, etc.)."""

    # Behavior
    max_retries: int = 3
    """Max retries for invalid tool calls or transient errors."""

    temperature: float = 0.7
    """Sampling temperature (0=deterministic, 1=max randomness)."""

    max_tokens: int = 4096
    """Max tokens in response."""

    # Tool configuration
    tool_use_enabled: bool = True
    """Enable structured tool use (vs raw text output)."""

    tool_choice: str = "auto"
    """Tool selection strategy (auto=let model decide, required=must use tool, none=no tools)."""

    # Advanced
    timeout_seconds: int = 300
    """Request timeout in seconds."""

    metadata: dict[str, Any] | None = None
    """Backend-specific configuration."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ToolSchema:
    """Tool schema for registration with orchestrator."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        required: list[str] | None = None,
    ):
        """
        Initialize tool schema.

        Args:
            name: Tool name
            description: Human-readable description
            parameters: JSON schema for parameters ({"properties": {...}, ...})
            required: List of required parameter names
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.required = required or []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters.get("properties", {}),
                "required": self.required,
            },
        }

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters.get("properties", {}),
                    "required": self.required,
                },
            },
        }


class OrchestratorBackend(ABC):
    """Abstract base class for orchestrator implementations."""

    def __init__(self, config: OrchestratorConfig):
        """Initialize backend with configuration."""
        self.config = config

    @abstractmethod
    def register_tools(self, tools: list[ToolSchema]) -> None:
        """
        Register available tools for the planner.

        Args:
            tools: List of ToolSchema objects
        """
        pass

    @abstractmethod
    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """
        Generate a plan (thinking + tool calls).

        Args:
            user_message: User request/message
            conversation_history: Optional conversation history for context
            system_prompt: Optional system instructions for the model

        Returns:
            PlanResult with reasoning and tool calls
        """
        pass

    @abstractmethod
    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        """
        Generate a plan with streaming response.

        Args:
            user_message: User request/message
            conversation_history: Optional conversation history

        Yields:
            Stream events (format backend-specific)
        """
        pass

    def add_tool_result(  # noqa: B027
        self,
        tool_call_id: str,
        result: str | dict[str, Any],
        is_error: bool = False,
    ) -> None:
        """
        Add tool execution result to conversation history.

        Args:
            tool_call_id: ID of the tool call being responded to
            result: Result from tool execution (success or error message)
            is_error: Whether result is an error
        """
        pass  # noqa: B027

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get current conversation history."""
        return []

    def clear_conversation_history(self) -> None:  # noqa: B027
        """Clear conversation history."""
        pass  # noqa: B027


__all__ = [
    "ToolCall",
    "PlanResult",
    "OrchestratorConfig",
    "ToolSchema",
    "OrchestratorBackend",
]
