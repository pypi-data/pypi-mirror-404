"""
Native OpenAI/Azure OpenAI Orchestrator

Implements OrchestratorBackend using the official `openai` Python SDK.
Supports both standard OpenAI and Azure OpenAI via configuration.

Features:
- Unified adapter for OpenAI-compatible endpoints
- Azure OpenAI support (via api_type="azure" or presence of api_version)
- Standard OpenAI support
- Full tool use support via OpenAI function calling format

Usage:
    from orchestrator.adapters.openai_native import OpenAINativeOrchestrator
    from orchestrator.adapters.orchestrator_interface import OrchestratorConfig

    # Standard OpenAI
    config = OrchestratorConfig(
        model="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Azure OpenAI
    azure_config = OrchestratorConfig(
        model="my-deployment",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        metadata={"api_version": "2024-05-01-preview", "api_type": "azure"}
    )

    orchestrator = OpenAINativeOrchestrator(config)
"""

import json
import logging
import os
from typing import TYPE_CHECKING, Any, cast

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)

# Optional dependency
if TYPE_CHECKING:
    from openai import AzureOpenAI, OpenAI, Stream
    from openai.types.chat import ChatCompletionMessageParam
else:
    AzureOpenAI = None
    OpenAI = None
    Stream = None
    ChatCompletionMessageParam = Any
    try:
        from openai import AzureOpenAI, OpenAI
        from openai.types.chat import ChatCompletionMessageParam
    except ImportError:
        pass

logger = logging.getLogger(__name__)


class OpenAINativeOrchestrator(OrchestratorBackend):
    """Native OpenAI/Azure orchestrator (no LiteLLM)."""

    if TYPE_CHECKING:
        client: OpenAI | AzureOpenAI
    else:
        client: Any

    def __init__(self, config: OrchestratorConfig):
        """Initialize OpenAI/Azure orchestrator.

        Args:
            config: OrchestratorConfig.
                - metadata["api_type"]: "azure" or "openai" (default: "openai" unless azure params detected)
                - metadata["api_version"]: Required for Azure
        """
        super().__init__(config)

        if OpenAI is None:
            raise ImportError(
                "openai SDK required for OpenAINativeOrchestrator. "
                "Install with: pip install openai"
            )

        self.tool_schemas: list[ToolSchema] = []
        self.conversation_history: list[dict[str, Any]] = []
        self.max_retries = config.max_retries

        # Determine API Type (Strict Mode)
        metadata = config.metadata or {}
        api_type = metadata.get("api_type", "openai")

        # In strict mode, we do NOT auto-detect based on env vars or other metadata fields.
        # User must explicitly set api_type="azure" if they want Azure.

        self.api_type = api_type

        if self.api_type == "azure":
            self._init_azure(config, metadata)
        else:
            self._init_openai(config)

    def _init_azure(self, config: OrchestratorConfig, metadata: dict[str, Any]) -> None:
        api_key = config.api_key or os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = config.base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = metadata.get(
            "api_version",
            os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
        )

        if not api_key:
            raise ValueError("Azure API Key required (config.api_key or AZURE_OPENAI_API_KEY)")
        if not azure_endpoint:
            raise ValueError("Azure Endpoint required (config.base_url or AZURE_OPENAI_ENDPOINT)")

        logger.info(
            f"OpenAINativeOrchestrator initialized (Azure): "
            f"deployment={config.model}, endpoint={azure_endpoint}, version={api_version}"
        )

        if AzureOpenAI is None:
            raise ImportError("openai package not installed")
        self.client = cast(Any, AzureOpenAI)(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
        )

    def _init_openai(self, config: OrchestratorConfig) -> None:
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        base_url = config.base_url or os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise ValueError("OpenAI API Key required (config.api_key or OPENAI_API_KEY)")

        logger.info(f"OpenAINativeOrchestrator initialized (OpenAI): model={config.model}")

        if OpenAI is None:
            raise ImportError("openai package not installed")
        self.client = cast(Any, OpenAI)(
            api_key=api_key,
            base_url=base_url,
        )

    def register_tools(self, tools: list[ToolSchema]) -> None:
        """Register tools for planning."""
        self.tool_schemas = tools

    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """
        Generate a plan using OpenAI/Azure OpenAI.
        """
        # Prepare messages
        messages: list[ChatCompletionMessageParam] = []

        # System Prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # History
        history_to_use = conversation_history or self.conversation_history

        # Adapt history to OpenAI format if needed
        # We assume history is already compatible-ish usually, but strict typing helps
        # For this implementation we cast/trust the inputs to match strict requirement or close enough

        # If history comes from our own internal state, it is compatible.
        # If it comes from external simpler dicts, we pass them.
        for msg in history_to_use:
            messages.append(cast(ChatCompletionMessageParam, msg))

        # Current user message
        messages.append({"role": "user", "content": user_message})

        # Prepare tools
        openai_tools = [t.to_openai_format() for t in self.tool_schemas]

        # Call API
        try:
            client = cast(Any, self.client)
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            logger.error(f"OpenAI/Azure Error: {e}")
            return PlanResult(
                reasoning=f"Error during planning: {str(e)}",
                tool_calls=[],
                stop_reason="error"
            )

        message = response.choices[0].message
        stop_reason = response.choices[0].finish_reason

        # Extract reasoning (content)
        reasoning = message.content or ""

        # Extract tool calls
        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                fn = tc.function
                try:
                    args = json.loads(fn.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(ToolCall(
                    tool_name=fn.name,
                    parameters=args,
                    id=tc.id
                ))

        # Update internal history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Convert response message to dict for history
        assistant_msg = {"role": "assistant", "content": reasoning}
        if message.tool_calls:
             assistant_msg["tool_calls"] = [
                 tc.model_dump() for tc in message.tool_calls
             ]

        self.conversation_history.append(assistant_msg)

        return PlanResult(
            reasoning=reasoning,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            metadata={
                "usage": response.usage.model_dump() if response.usage else {},
                "model": response.model
            }
        )

    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        """Stream planning (Not implemented)."""
        raise NotImplementedError("Streaming not yet supported for OpenAINativeOrchestrator.")

    def add_tool_result(
        self,
        tool_call_id: str,
        result: str | dict[str, Any],
        is_error: bool = False,
    ) -> None:
        """Add tool result to history."""
        content = json.dumps(result) if isinstance(result, (dict, list)) else str(result)

        self.conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def get_conversation_history(self) -> list[dict[str, str]]:
        return cast(list[dict[str, str]], self.conversation_history)

    def clear_conversation_history(self) -> None:
        self.conversation_history = []
