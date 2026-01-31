"""
Claude SDK Orchestrator (Phase 5.2)

Implements OrchestratorBackend using Anthropic Claude SDK.

Features:
- Vendor-neutral tool schema → Claude SDK format conversion
- Streaming and non-streaming planning
- Error handling and retry logic
- Conversation history management
- Token tracking and cost estimation

Usage:
    from orchestrator.adapters import ClaudeOrchestrator, OrchestratorConfig

    config = OrchestratorConfig(
        model="claude-3-5-sonnet-20241022",
        api_key="sk-ant-...",  # or ANTHROPIC_API_KEY env var
    )
    orchestrator = ClaudeOrchestrator(config)

    # Register tools
    orchestrator.register_tools(tool_schemas)

    # Plan
    result = orchestrator.plan("Extract text from this image")
    print(result.reasoning)
    for tool_call in result.tool_calls:
        print(f"  - {tool_call.tool_name}({tool_call.parameters})")
"""

import logging
import os
from typing import Any

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)

logger = logging.getLogger(__name__)


class ClaudeOrchestrator(OrchestratorBackend):
    """Claude SDK-based orchestrator."""

    def __init__(self, config: OrchestratorConfig):
        """Initialize Claude orchestrator.

        Args:
            config: OrchestratorConfig with model, API key, etc.
        """
        super().__init__(config)

        # Import Anthropic SDK (optional dependency)
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic SDK required for ClaudeOrchestrator. "
                "Install with: pip install anthropic"
            ) from e

        self.anthropic = anthropic

        # Initialize client
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "API key required: pass api_key in config or set ANTHROPIC_API_KEY env var"
            )

        # Handle base_url for proxy scenarios (e.g., LiteLLM)
        if config.base_url:
            self.client = self.anthropic.Anthropic(
                api_key=api_key,
                base_url=config.base_url,
            )
        else:
            self.client = self.anthropic.Anthropic(api_key=api_key)

        self.tool_schemas: list[ToolSchema] = []
        self.conversation_history: list[dict[str, Any]] = []
        self.max_retries = config.max_retries

        logger.info(
            f"ClaudeOrchestrator initialized: "
            f"model={config.model}, "
            f"base_url={config.base_url or 'default'}"
        )

    def register_tools(self, tools: list[ToolSchema]) -> None:
        """Register tools for planning.

        Args:
            tools: List of ToolSchema objects
        """
        self.tool_schemas = tools
        logger.info(f"Registered {len(tools)} tools")

    def _convert_to_claude_tools(self) -> list[dict[str, Any]]:
        """Convert tool schemas to Claude SDK format.

        Claude SDK uses:
        {
            "name": str,
            "description": str,
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        tools = []
        for schema in self.tool_schemas:
            tool_def = {
                "name": schema.name,
                "description": schema.description,
                "input_schema": {
                    "type": "object",
                    "properties": schema.parameters.get("properties", {}),
                    "required": schema.required,
                },
            }
            tools.append(tool_def)
        return tools

    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """Generate a plan using Claude.

        Args:
            user_message: User request/message
            conversation_history: Optional conversation history
            system_prompt: Optional system instructions

        Returns:
            PlanResult with reasoning and tool calls
        """
        # Use provided history or internal history
        if conversation_history is not None:
            history = conversation_history
        else:
            history = self.conversation_history

        # Build messages
        messages = []
        for msg in history:
            messages.append(msg)

        # Only add user message if non-empty (for follow-up calls)
        if user_message:
            messages.append({"role": "user", "content": user_message})

        # Store in conversation history
        self.conversation_history = messages

        # Build API call params
        api_params = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "tools": self._convert_to_claude_tools(),
            "messages": messages,
        }

        # Add system prompt if provided
        if system_prompt:
            api_params["system"] = system_prompt

        # Call Claude
        try:
            response = self.client.messages.create(**api_params)  # type: ignore[call-overload]
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

        # Extract thinking and tool calls
        reasoning = ""
        tool_calls: list[ToolCall] = []

        for block in response.content:
            # Extract thinking/reasoning
            if hasattr(block, "type"):
                if block.type == "thinking":
                    reasoning = getattr(block, "thinking", "")
                elif block.type == "text":
                    reasoning = getattr(block, "text", "")
                elif block.type == "tool_use":
                    # Extract tool call
                    tool_call = ToolCall(
                        tool_name=block.name,
                        parameters=block.input or {},
                        id=block.id,
                    )
                    tool_calls.append(tool_call)

        # Determine stop reason
        stop_reason = response.stop_reason or "tool_use"

        # Build metadata
        metadata = {}
        if hasattr(response, "usage"):
            usage = response.usage
            metadata["input_tokens"] = usage.input_tokens
            metadata["output_tokens"] = usage.output_tokens
            # Rough estimate: Claude pricing ~$0.003 per 1K input, $0.015 per 1K output
            metadata["cost_estimate_usd"] = (
                (usage.input_tokens / 1000) * 0.003 +
                (usage.output_tokens / 1000) * 0.015
            )

        result = PlanResult(
            reasoning=reasoning,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            metadata=metadata,
        )

        logger.info(
            f"Planning complete: "
            f"{len(tool_calls)} tool calls, "
            f"stop_reason={stop_reason}"
        )

        return result

    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        """Generate a plan with streaming response.

        Args:
            user_message: User request
            conversation_history: Optional conversation history

        Yields:
            Stream events with delta updates
        """
        history = conversation_history or []
        messages = []
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        self.conversation_history = messages

        try:
            with self.client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                tools=self._convert_to_claude_tools(),  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            ) as stream:
                for event in stream:
                    # Yield different event types
                    if hasattr(event, "type"):
                        if event.type == "content_block_start":
                            yield {
                                "type": "content_start",
                                "content_type": getattr(
                                    event.content_block, "type", "unknown"
                                ),
                            }
                        elif event.type == "content_block_delta":
                            if hasattr(event, "delta"):
                                yield {
                                    "type": "delta",
                                    "delta": event.delta,
                                }
                        elif event.type == "content_block_stop":
                            yield {"type": "content_stop"}
                        elif event.type == "message_stop":
                            yield {"type": "message_stop"}
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise

    def add_tool_result(
        self,
        tool_call_id: str,
        result: str | dict[str, Any],
        is_error: bool = False,
    ) -> None:
        """Add tool execution result to conversation.

        Args:
            tool_call_id: ID of the tool call
            result: Result from tool execution
            is_error: Whether result is an error
        """
        # Convert result to string if dict
        result_str = result if isinstance(result, str) else str(result)

        # Add to conversation history
        self.conversation_history.append(
            {
                "type": "tool_result",
                "tool_use_id": tool_call_id,
                "content": result_str,
                "is_error": is_error,
            }
        )

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []


__all__ = ["ClaudeOrchestrator"]
