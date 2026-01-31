"""
Tests for OpenAI/Azure Native Orchestrator

Verifies:
- Initialization with config (Azure and OpenAI modes)
- Planning via OpenAI SDK mock
- Tool schema conversion
- History management
"""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.adapters.openai_native import OpenAINativeOrchestrator
from orchestrator.adapters.orchestrator_interface import (
    OrchestratorConfig,
    ToolSchema,
)

pytest.importorskip("openai")


@pytest.fixture
def azure_config() -> Any:
    return OrchestratorConfig(
        model="gpt-4o-deploy",
        api_key="fake-key",
        base_url="https://fake.openai.azure.com",
        metadata={
            "api_version": "2024-05-01-preview",
            "api_type": "azure"
        }
    )


@patch("orchestrator.adapters.openai_native.AzureOpenAI")
def test_initialization_azure(mock_client: Any, azure_config: Any) -> None:
    """Test initialization with explicit config for Azure."""
    orch = OpenAINativeOrchestrator(azure_config)
    assert orch.client is not None
    assert orch.api_type == "azure"
    mock_client.assert_called_once()


@patch("orchestrator.adapters.openai_native.OpenAI")
def test_initialization_openai(mock_client: Any) -> None:
    """Test initialization for standard OpenAI."""
    config = OrchestratorConfig(
        model="gpt-4",
        api_key="sk-fake",
        metadata={"api_type": "openai"}
    )
    orch = OpenAINativeOrchestrator(config)
    assert orch.client is not None
    assert orch.api_type == "openai"
    mock_client.assert_called_once()


@patch("orchestrator.adapters.openai_native.AzureOpenAI")
def test_initialization_env_vars_azure(mock_client: Any, monkeypatch: Any) -> None:
    """Test initialization with environment variables (implied Azure)."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://env.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

    # Strict mode requires explicit api_type currently,
    # OR we need to update the OrchestratorConfig setup in the test to include it.
    config = OrchestratorConfig(
        model="gpt-4",
        metadata={"api_type": "azure"}
    )
    orch = OpenAINativeOrchestrator(config)

    assert orch.api_type == "azure"
    mock_client.assert_called_with(
        api_key="env-key",
        api_version="2024-05-01-preview",
        azure_endpoint="https://env.azure.com"
    )


@patch("orchestrator.adapters.openai_native.AzureOpenAI")
def test_plan_simple(mock_client: Any, azure_config: Any) -> None:
    """Test simple planning with a text response (Azure)."""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="I am ready.",
                tool_calls=None
            ),
            finish_reason="stop"
        )
    ]
    mock_response.usage = MagicMock(model_dump=lambda: {"total_tokens": 10})
    mock_response.model = "gpt-4o"

    # Configure client mock
    instance = mock_client.return_value
    instance.chat.completions.create.return_value = mock_response

    orch = OpenAINativeOrchestrator(azure_config)

    result = orch.plan("Hello")

    assert result.reasoning == "I am ready."
    assert result.tool_calls == []
    assert result.stop_reason == "stop"

    # Verify call structure
    instance.chat.completions.create.assert_called_once()
    args, kwargs = instance.chat.completions.create.call_args
    assert kwargs["messages"][-1]["content"] == "Hello"


@patch("orchestrator.adapters.openai_native.AzureOpenAI")
def test_plan_with_tools(mock_client: Any, azure_config: Any) -> None:
    """Test planning with tool execution (Azure)."""
    # Mock tool response
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "get_weather"
    mock_tool_call.function.arguments = '{"city": "Seattle"}'
    mock_tool_call.id = "call_123"

    # Needs model_dump for history preservation
    mock_tool_call.model_dump.return_value = {
        "id": "call_123",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"city": "Seattle"}'}
    }

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Checking weather...",
                tool_calls=[mock_tool_call]
            ),
            finish_reason="tool_calls"
        )
    ]

    instance = mock_client.return_value
    instance.chat.completions.create.return_value = mock_response

    orch = OpenAINativeOrchestrator(azure_config)

    # Register tool
    schema = ToolSchema(
        name="get_weather",
        description="Get city weather",
        parameters={"properties": {"city": {"type": "string"}}}
    )
    orch.register_tools([schema])

    result = orch.plan("Weather in Seattle?")

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_weather"
    assert result.tool_calls[0].parameters == {"city": "Seattle"}

    # Verify internal history includes tool call
    history = orch.get_conversation_history()
    assert len(history) == 2  # user + assistant
    assert "tool_calls" in history[1]


@patch("orchestrator.adapters.openai_native.AzureOpenAI")
def test_add_tool_result(mock_client: Any, azure_config: Any) -> None:
    """Test adding tool results to history."""
    orch = OpenAINativeOrchestrator(azure_config)

    orch.add_tool_result("call_123", {"temperature": 72})

    history = orch.get_conversation_history()
    assert len(history) == 1
    assert history[0]["role"] == "tool"
    assert history[0]["tool_call_id"] == "call_123"
    assert json.loads(history[0]["content"]) == {"temperature": 72}
