"""Test final_synthesis functionality."""

import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestrator._internal.runtime.orchestrator import final_synthesis


class TestFinalSynthesis:
    """Test suite for final_synthesis function."""

    @pytest.mark.asyncio
    async def test_final_synthesis_openai(self) -> None:
        """Test final_synthesis with OpenAI provider."""
        plan: dict[str, Any] = {
            "request_id": "test-123",
            "final_synthesis": {
                "prompt_template": "Summarize the results",
                "meta": {"test": True},
            },
        }

        context: dict[str, Any] = {
            "step-1": {"status": "success", "data": "result1"},
            "step-2": {"status": "success", "data": "result2"},
        }

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test synthesis response."

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator._internal.runtime.orchestrator.AsyncOpenAI", return_value=mock_client):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                result = await final_synthesis(plan, context, provider="openai", model="gpt-4o")

        assert "synthesis" in result
        assert result["synthesis"] == "This is a test synthesis response."

        # Verify the API was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["temperature"] == 0.3
        assert len(call_kwargs["messages"]) == 2

    @pytest.mark.asyncio
    async def test_final_synthesis_anthropic(self) -> None:
        """Test final_synthesis with Anthropic provider."""
        plan: dict[str, Any] = {
            "request_id": "test-456",
            "final_synthesis": {
                "prompt_template": "Explain what happened",
            },
        }

        context: dict[str, Any] = {
            "step-1": {"result": "completed task A"},
        }

        # Mock Anthropic response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Task A was completed successfully."

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator._internal.runtime.orchestrator.anthropic.AsyncAnthropic", return_value=mock_client):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                result = await final_synthesis(plan, context, provider="anthropic", model="claude-3-5-sonnet-20241022")

        assert "synthesis" in result
        assert result["synthesis"] == "Task A was completed successfully."

        # Verify the API was called
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_final_synthesis_fallback_on_error(self) -> None:
        """Test that final_synthesis falls back gracefully on API error."""
        plan: dict[str, Any] = {
            "request_id": "test-789",
            "final_synthesis": {
                "prompt_template": "Summarize execution",
            },
        }

        context: dict[str, Any] = {
            "step-1": {"output": "data1"},
        }

        # Mock API to raise an exception
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        with patch("orchestrator._internal.runtime.orchestrator.AsyncOpenAI", return_value=mock_client):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                result = await final_synthesis(plan, context, provider="openai", model="gpt-4o")

        # Should return fallback
        assert "synthesis" in result
        assert "Summarize execution" in result["synthesis"]
        assert json.dumps(context, indent=2) in result["synthesis"]

    @pytest.mark.asyncio
    async def test_final_synthesis_empty_template(self) -> None:
        """Test final_synthesis with missing template uses default."""
        plan: dict[str, Any] = {
            "request_id": "test-default",
            "final_synthesis": {},
        }

        context: dict[str, Any] = {
            "step-1": {"done": True},
        }

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Default synthesis."

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator._internal.runtime.orchestrator.AsyncOpenAI", return_value=mock_client):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                result = await final_synthesis(plan, context, provider="openai", model="gpt-4o-mini")

        assert "synthesis" in result

        # Verify default template was used
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        user_message = call_kwargs["messages"][1]["content"]
        assert "Summarize the execution results" in user_message
