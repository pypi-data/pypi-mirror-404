"""
Tests for Monitoring Hooks Integration.

Phase 5.5.4: Verifies that the AgenticExecutor correctly emits
monitoring events (metrics) during execution.
"""

import os
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.adapters.agentic_executor import AgenticExecutor
from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
)


class MockOrchestrator(OrchestratorBackend):
    """Mock orchestrator for testing."""

    def __init__(self, config: OrchestratorConfig) -> None:
        super().__init__(config)
        self.plan_results: list[PlanResult] = []
        self.current_plan_index = 0

    def register_tools(self, tools: list[Any]) -> None:
        pass

    def plan(
        self,
        user_message: str,
        conversation_history: list[Any] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        if self.current_plan_index < len(self.plan_results):
            result = self.plan_results[self.current_plan_index]
            self.current_plan_index += 1
            return result
        return PlanResult(
            reasoning="Done",
            tool_calls=[],
            stop_reason="end_turn",
        )

    def plan_streaming(self, *args: Any, **kwargs: Any) -> Iterator[dict[str, str]]:
        yield {"type": "message_stop"}

    def add_tool_result(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get_conversation_history(self) -> list[dict[str, str]]:
        return []

    def clear_conversation_history(self) -> None:
        pass


@pytest.mark.asyncio
async def test_monitoring_hooks_fired_during_execution() -> None:
    """Test that monitoring hooks are called during execution."""
    # Setup mocks
    model = os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022")
    config = OrchestratorConfig(model=model)
    orchestrator = MockOrchestrator(config)
    executor = AgenticExecutor(orchestrator)

    # Configure plan: 1 tool call, then finish
    orchestrator.plan_results = [
        PlanResult(
            reasoning="Calling tool",
            tool_calls=[
                ToolCall(id="t1", tool_name="test_tool", parameters={"arg": "val"})
            ],
            stop_reason="tool_use",
        ),
        PlanResult(
            reasoning="Done",
            tool_calls=[],
            stop_reason="end_turn",
        ),
    ]

    # Mock tool execution
    with patch("orchestrator.tools.tool_executor.call_tool") as mock_call_tool:
        mock_call_tool.return_value = "Success"

        # Mock Observability
        mock_obs = MagicMock()
        with patch(
            "orchestrator.observability.get_observability", return_value=mock_obs
        ):
            # Run execution
            await executor.execute_task("Run test")

            # Verify events
            # 1. Agent Start
            # 2. Agent Step (Plan 1)
            # 3. Tool Execution
            # 4. Agent Step (Plan 2)
            # 5. Agent Completion

            assert mock_obs.log_event.call_count >= 5

            calls = [c[0][0] for c in mock_obs.log_event.call_args_list]

            # Check for start
            assert any(e["event_type"] == "agent_start" for e in calls)

            # Check for tool execution
            tool_events = [e for e in calls if e["event_type"] == "tool_execution"]
            assert len(tool_events) == 1
            assert tool_events[0]["tool_name"] == "test_tool"
            assert tool_events[0]["success"] is True
            assert "duration_ms" in tool_events[0]

            # Check for completion
            completion = [e for e in calls if e["event_type"] == "agent_completion"][0]
            assert completion["success"] is True
            assert completion["iterations"] == 2
            assert "duration_ms" in completion


def test_monitoring_hooks_methods() -> None:
    """Test MonitoringHooks static methods directly."""
    with patch("orchestrator.observability.get_observability") as mock_get:
        mock_obs = MagicMock()
        mock_get.return_value = mock_obs

        from orchestrator.observability import MonitoringHooks

        # Test record_agent_start
        MonitoringHooks.record_agent_start("Task 1", "sess-1")
        mock_obs.log_event.assert_called_with(
            {
                "event_type": "agent_start",
                "task_snippet": "Task 1",
                "session_id": "sess-1",
            }
        )

        # Test record_tool_call
        MonitoringHooks.record_tool_call("tool1", 100.0, True)
        mock_obs.log_event.assert_called_with(
            {
                "event_type": "tool_execution",
                "tool_name": "tool1",
                "duration_ms": 100.0,
                "success": True,
            }
        )

        # Test record_agent_completion with error
        MonitoringHooks.record_agent_completion(False, 5, 2000.0, 100, "Error")
        mock_obs.log_event.assert_called_with(
            {
                "event_type": "agent_completion",
                "success": False,
                "iterations": 5,
                "duration_ms": 2000.0,
                "total_tokens": 100,
                "error": "Error",
            }
        )


@pytest.mark.asyncio
async def test_monitoring_failure_scenario() -> None:
    """Test monitoring during failure execution."""
    model = os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022")
    config = OrchestratorConfig(model=model)
    orchestrator = MockOrchestrator(config)
    executor = AgenticExecutor(orchestrator)

    # Mock orchestrator to fail
    orchestrator.plan = MagicMock(side_effect=Exception("Plan failed"))  # type: ignore[method-assign]

    with patch("orchestrator.observability.get_observability") as mock_get:
        mock_obs = MagicMock()
        mock_get.return_value = mock_obs

        await executor.execute_task("Fail task")

        calls = [c[0][0] for c in mock_obs.log_event.call_args_list]

        # Should start
        assert any(e["event_type"] == "agent_start" for e in calls)

        # Should fail complete
        completion = [e for e in calls if e["event_type"] == "agent_completion"][0]
        assert completion["success"] is False
        assert completion["error"] == "Plan failed"

