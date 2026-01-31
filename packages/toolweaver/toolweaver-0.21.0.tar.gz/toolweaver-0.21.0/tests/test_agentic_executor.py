"""
Tests for AgenticExecutor - End-to-end agentic loop

Tests cover:
- Basic agentic loop execution
- Tool execution and result handling
- Error recovery and feedback
- Conversation history management
- Multi-turn interactions
- Iteration limits and termination
"""

import os
from typing import Any
from unittest.mock import patch

import pytest

from orchestrator.adapters.agentic_executor import AgenticExecutor, AgenticResult
from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)


class MockOrchestrator(OrchestratorBackend):
    """Mock orchestrator for testing."""

    def __init__(self, config: OrchestratorConfig) -> None:
        super().__init__(config)
        self.tools: list[ToolSchema] = []
        self.conversation_history: list[dict[str, Any]] = []
        self.plan_results: list[PlanResult] = []
        self.current_plan_index = 0

    def register_tools(self, tools: list[ToolSchema]) -> None:
        self.tools = tools

    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """Return pre-configured plan results."""
        if self.current_plan_index < len(self.plan_results):
            result = self.plan_results[self.current_plan_index]
            self.current_plan_index += 1
            return result
        # Default: end turn
        return PlanResult(
            reasoning="Task complete",
            tool_calls=[],
            stop_reason="end_turn",
        )

    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        yield {"type": "message_stop"}

    def add_tool_result(
        self,
        tool_call_id: str,
        result: str | dict[str, Any],
        is_error: bool = False,
    ) -> None:
        self.conversation_history.append(
            {
                "tool_call_id": tool_call_id,
                "result": result,
                "is_error": is_error,
            }
        )

    def get_conversation_history(self) -> list[dict[str, str]]:
        return self.conversation_history

    def clear_conversation_history(self) -> None:
        self.conversation_history = []


class TestAgenticExecutor:
    """Test AgenticExecutor."""

    def test_init(self) -> None:
        """Test initialization."""
        # Load test model from environment (TEST_MODEL_NAME)
        model = os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022")
        config = OrchestratorConfig(model=model)
        orchestrator = MockOrchestrator(config)
        executor = AgenticExecutor(orchestrator)

        assert executor.orchestrator == orchestrator
        assert executor.system_prompt is not None
        assert executor._iteration_count == 0

    def test_register_tools(self) -> None:
        """Test tool registration."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)
        executor = AgenticExecutor(orchestrator)

        tools = [
            ToolSchema(
                name="get_weather",
                description="Get weather",
                parameters={"location": {"type": "string"}},
            )
        ]
        executor.register_tools(tools)

        assert len(orchestrator.tools) == 1
        assert orchestrator.tools[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_simple_task_no_tools(self) -> None:
        """Test task that completes without tools."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        # Pre-configure plan: complete immediately
        orchestrator.plan_results = [
            PlanResult(
                reasoning="The answer is 42",
                tool_calls=[],
                stop_reason="end_turn",
            )
        ]

        executor = AgenticExecutor(orchestrator)
        result = await executor.execute_task("What is the answer?")

        assert result.success is True
        assert result.iterations == 1
        assert result.final_response == "The answer is 42"
        assert len(result.tool_calls) == 0

    @pytest.mark.asyncio
    async def test_task_with_single_tool(self) -> None:
        """Test task with one tool call."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        # Plan: call tool, then complete
        orchestrator.plan_results = [
            PlanResult(
                reasoning="I need to get the weather",
                tool_calls=[
                    ToolCall(
                        tool_name="get_weather",
                        parameters={"location": "Paris"},
                        id="tool_1",
                    )
                ],
                stop_reason="tool_use",
            ),
            PlanResult(
                reasoning="The weather in Paris is sunny",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        # Mock tool execution
        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            mock_call.return_value = {"weather": "sunny", "temp": 72}

            result = await executor.execute_task("What's the weather in Paris?")

        assert result.success is True
        assert result.iterations == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "get_weather"
        assert len(result.tool_results) == 1
        assert result.tool_results[0]["success"] is True

    @pytest.mark.asyncio
    async def test_task_with_multiple_tools(self) -> None:
        """Test task with multiple tool calls."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        # Plan: call 2 tools, then complete
        orchestrator.plan_results = [
            PlanResult(
                reasoning="I need weather and currency",
                tool_calls=[
                    ToolCall(tool_name="get_weather", parameters={"location": "Paris"}, id="t1"),
                    ToolCall(tool_name="convert_currency", parameters={"from": "USD", "to": "EUR"}, id="t2"),
                ],
                stop_reason="tool_use",
            ),
            PlanResult(
                reasoning="Weather is sunny, 72°F costs 65€",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            # Return different results for each tool
            mock_call.side_effect = [
                {"weather": "sunny", "temp": 72},
                {"amount": 65, "currency": "EUR"},
            ]

            result = await executor.execute_task("Weather and currency for Paris?")

        assert result.success is True
        assert result.iterations == 2
        assert len(result.tool_calls) == 2
        assert len(result.tool_results) == 2

    @pytest.mark.asyncio
    async def test_tool_error_recovery(self) -> None:
        """Test error recovery when tool fails."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        orchestrator.plan_results = [
            # First plan: call tool
            PlanResult(
                reasoning="Getting weather",
                tool_calls=[
                    ToolCall(tool_name="get_weather", parameters={"location": "InvalidCity"}, id="t1")
                ],
                stop_reason="tool_use",
            ),
            # Second plan: handle error and complete
            PlanResult(
                reasoning="City not found, providing generic response",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            # Simulate tool error
            mock_call.side_effect = ValueError("City not found")

            result = await executor.execute_task("Weather in InvalidCity?")

        assert result.success is True
        assert result.iterations == 2
        assert len(result.tool_results) == 1
        assert result.tool_results[0]["success"] is False
        assert "City not found" in result.tool_results[0]["error"]

        # Check that error was sent to orchestrator
        assert len(orchestrator.conversation_history) == 1
        assert orchestrator.conversation_history[0]["is_error"] is True

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self) -> None:
        """Test max iterations limit."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        # Keep returning tool calls (infinite loop)
        orchestrator.plan_results = [
            PlanResult(
                reasoning="Keep calling",
                tool_calls=[ToolCall(tool_name="tool", parameters={}, id=f"t{i}")],
                stop_reason="tool_use",
            )
            for i in range(20)  # More than max_iterations
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            mock_call.return_value = {"result": "ok"}

            result = await executor.execute_task("Endless task", max_iterations=3)

        assert result.success is False
        assert result.iterations == 3
        assert result.error == "max_iterations_reached"
        assert len(result.tool_calls) == 3  # 3 iterations, 1 tool each

    @pytest.mark.asyncio
    async def test_conversation_history(self) -> None:
        """Test conversation history tracking."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        orchestrator.plan_results = [
            PlanResult(
                reasoning="Calling tool",
                tool_calls=[ToolCall(tool_name="tool", parameters={}, id="t1")],
                stop_reason="tool_use",
            ),
            PlanResult(
                reasoning="Done",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            mock_call.return_value = {"result": "success"}

            await executor.execute_task("Task")

        # Check conversation history
        history = executor.get_conversation_history()
        assert len(history) == 1
        assert history[0]["tool_call_id"] == "t1"
        assert history[0]["result"] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_clear_history(self) -> None:
        """Test clearing history and state."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        orchestrator.plan_results = [
            PlanResult(
                reasoning="Done",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        # Execute task
        await executor.execute_task("Task")

        # Verify state exists
        assert executor._iteration_count > 0

        # Clear
        executor.clear_history()

        # Verify cleared
        assert executor._iteration_count == 0
        assert len(executor._all_tool_calls) == 0
        assert len(executor._all_tool_results) == 0
        assert len(orchestrator.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_multi_turn_interaction(self) -> None:
        """Test multi-turn conversation with tools."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        # Turn 1: Get weather
        orchestrator.plan_results = [
            PlanResult(
                reasoning="Getting weather",
                tool_calls=[ToolCall(tool_name="get_weather", parameters={"city": "Paris"}, id="t1")],
                stop_reason="tool_use",
            ),
            # Turn 2: Convert temp
            PlanResult(
                reasoning="Converting temperature",
                tool_calls=[ToolCall(tool_name="convert_temp", parameters={"from": "C", "to": "F"}, id="t2")],
                stop_reason="tool_use",
            ),
            # Turn 3: Done
            PlanResult(
                reasoning="Paris is 72°F",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            mock_call.side_effect = [
                {"temp": 22, "unit": "C"},  # Weather result
                {"temp": 72, "unit": "F"},  # Conversion result
            ]

            result = await executor.execute_task("Weather in Paris in Fahrenheit?")

        assert result.success is True
        assert result.iterations == 3
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].tool_name == "get_weather"
        assert result.tool_calls[1].tool_name == "convert_temp"

    @pytest.mark.asyncio
    async def test_custom_system_prompt(self) -> None:
        """Test custom system prompt."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        custom_prompt = "You are a specialized weather assistant"

        orchestrator.plan_results = [
            PlanResult(reasoning="Done", tool_calls=[], stop_reason="end_turn"),
        ]

        executor = AgenticExecutor(orchestrator, system_prompt=custom_prompt)
        await executor.execute_task("Task")

        assert executor.system_prompt == custom_prompt

    @pytest.mark.asyncio
    async def test_tool_timeout(self) -> None:
        """Test tool execution timeout handling."""
        config = OrchestratorConfig(model=os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022"))
        orchestrator = MockOrchestrator(config)

        orchestrator.plan_results = [
            PlanResult(
                reasoning="Calling slow tool",
                tool_calls=[ToolCall(tool_name="slow_tool", parameters={}, id="t1")],
                stop_reason="tool_use",
            ),
            PlanResult(
                reasoning="Handling timeout",
                tool_calls=[],
                stop_reason="end_turn",
            ),
        ]

        executor = AgenticExecutor(orchestrator)

        with patch("orchestrator.tools.tool_executor.call_tool") as mock_call:
            # Simulate timeout
            import asyncio
            mock_call.side_effect = asyncio.TimeoutError("Tool timed out")

            result = await executor.execute_task("Task", tool_timeout=5)

        assert result.success is True  # Executor handled timeout
        assert result.tool_results[0]["success"] is False
        assert "timed out" in result.tool_results[0]["error"].lower()


class TestAgenticResult:
    """Test AgenticResult dataclass."""

    def test_success_result(self) -> None:
        """Test success result creation."""
        result = AgenticResult(
            success=True,
            final_response="Task completed",
            iterations=3,
            tool_calls=[],
            tool_results=[],
        )

        assert result.success is True
        assert result.error is None

    def test_error_result(self) -> None:
        """Test error result creation."""
        result = AgenticResult(
            success=False,
            final_response="",
            iterations=1,
            tool_calls=[],
            tool_results=[],
            error="Test error",
        )

        assert result.success is False
        assert result.error == "Test error"

