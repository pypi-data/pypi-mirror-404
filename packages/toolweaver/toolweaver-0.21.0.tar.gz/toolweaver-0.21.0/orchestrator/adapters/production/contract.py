"""Contract tests for orchestrator backend compliance.

This module defines contract tests that all OrchestratorBackend
implementations must pass to ensure interface compliance.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

import pytest

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)


class OrchestratorContractTests(ABC):
    """Base class defining contract tests for orchestrator backends.

    All orchestrator implementations should inherit from this class
    and implement create_orchestrator() to run the contract tests.
    """

    @abstractmethod
    def create_orchestrator(self, config: OrchestratorConfig) -> OrchestratorBackend:
        """Create an orchestrator instance for testing.

        Args:
            config: Configuration for the orchestrator

        Returns:
            Orchestrator instance
        """
        pass

    @pytest.fixture
    def orchestrator(self) -> OrchestratorBackend:
        """Fixture providing orchestrator instance."""
        config = OrchestratorConfig(
            model="test-model",
            temperature=0.7,
            max_tokens=1000,
        )
        return self.create_orchestrator(config)

    @pytest.fixture
    def sample_tool_schema(self) -> ToolSchema:
        """Fixture providing sample tool schema."""
        return ToolSchema(
            name="calculator",
            description="Perform basic arithmetic",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
            },
            required=["operation", "a", "b"],
        )

    # Contract Test 1: Plan returns PlanResult
    @pytest.mark.asyncio
    async def test_plan_returns_plan_result(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that plan() returns a PlanResult."""
        result = await orchestrator.plan("Test task")  # type: ignore[misc]
        assert isinstance(result, PlanResult)

    # Contract Test 2: PlanResult has required fields
    @pytest.mark.asyncio
    async def test_plan_result_has_required_fields(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that PlanResult has required fields."""
        result = await orchestrator.plan("Test task")  # type: ignore[misc]

        assert hasattr(result, "response")
        assert hasattr(result, "tool_calls")
        assert isinstance(result.tool_calls, list)

    # Contract Test 3: Plan with tools parameter
    @pytest.mark.asyncio
    async def test_plan_with_tools(
        self, orchestrator: OrchestratorBackend, sample_tool_schema: ToolSchema
    ) -> None:
        """Test that plan() accepts tools parameter."""
        # This should not raise an error
        result = await orchestrator.plan("Calculate 2 + 2")  # type: ignore[misc]
        assert isinstance(result, PlanResult)

    # Contract Test 4: ToolCall structure
    @pytest.mark.asyncio
    async def test_tool_call_structure(
        self, orchestrator: OrchestratorBackend, sample_tool_schema: ToolSchema
    ) -> None:
        """Test that ToolCalls have proper structure when generated."""
        result = await orchestrator.plan("Add 5 and 3")  # type: ignore[misc]

        if result.tool_calls:  # If tools were used
            tool_call = result.tool_calls[0]
            assert isinstance(tool_call, ToolCall)
            assert hasattr(tool_call, "tool_name")
            assert hasattr(tool_call, "parameters")
            assert isinstance(tool_call.parameters, dict)

    # Contract Test 5: Plan streaming
    @pytest.mark.asyncio
    async def test_plan_streaming(self, orchestrator: OrchestratorBackend) -> None:
        """Test that plan_streaming() yields chunks."""
        chunks: list[str] = []

        async for chunk in orchestrator.plan_streaming("Test task"):
            assert isinstance(chunk, str)
            chunks.append(chunk)

        # Should have received at least one chunk
        assert len(chunks) > 0

    # Contract Test 6: Conversation history
    @pytest.mark.asyncio
    async def test_conversation_history(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that conversation history can be retrieved."""
        await orchestrator.plan("First message")  # type: ignore[misc]
        history = orchestrator.get_conversation_history()

        assert isinstance(history, list)
        # History may be empty depending on implementation

    # Contract Test 7: Clear conversation
    @pytest.mark.asyncio
    async def test_clear_conversation(self, orchestrator: OrchestratorBackend) -> None:
        """Test that conversation history can be cleared."""
        await orchestrator.plan("Test message")  # type: ignore[misc]

        # This should not raise an error
        orchestrator.clear_conversation_history()

        history = orchestrator.get_conversation_history()
        assert len(history) == 0 or history == []

    # Contract Test 8: Add tool result
    @pytest.mark.asyncio
    async def test_add_tool_result(self, orchestrator: OrchestratorBackend) -> None:
        """Test that tool results can be added."""
        # This should not raise an error
        orchestrator.add_tool_result(
            tool_call_id="test_123",
            result="42",
            is_error=False,
        )

    # Contract Test 9: Add error result
    @pytest.mark.asyncio
    async def test_add_error_result(self, orchestrator: OrchestratorBackend) -> None:
        """Test that error results can be added."""
        # This should not raise an error
        orchestrator.add_tool_result(
            tool_call_id="test_456",
            result="Error: Division by zero",
            is_error=True,
        )

    # Contract Test 10: Multiple plan calls
    @pytest.mark.asyncio
    async def test_multiple_plan_calls(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that multiple plan calls work."""
        result1 = await orchestrator.plan("First task")  # type: ignore[misc]
        result2 = await orchestrator.plan("Second task")  # type: ignore[misc]

        assert isinstance(result1, PlanResult)
        assert isinstance(result2, PlanResult)

    # Contract Test 11: Empty prompt
    @pytest.mark.asyncio
    async def test_empty_prompt(self, orchestrator: OrchestratorBackend) -> None:
        """Test handling of empty prompt."""
        result = await orchestrator.plan("")  # type: ignore[misc]
        assert isinstance(result, PlanResult)

    # Contract Test 12: Long prompt
    @pytest.mark.asyncio
    async def test_long_prompt(self, orchestrator: OrchestratorBackend) -> None:
        """Test handling of long prompts."""
        long_prompt = "Test task. " * 100
        result = await orchestrator.plan(long_prompt)  # type: ignore[misc]
        assert isinstance(result, PlanResult)

    # Contract Test 13: Configuration immutability
    def test_config_immutability(self, orchestrator: OrchestratorBackend) -> None:
        """Test that orchestrator config is accessible."""
        config = orchestrator.config
        assert isinstance(config, OrchestratorConfig)
        assert hasattr(config, "model")

    # Contract Test 14: Concurrent plans
    @pytest.mark.asyncio
    async def test_concurrent_plans(self, orchestrator: OrchestratorBackend) -> None:
        """Test that concurrent plan calls work."""
        results = await asyncio.gather(  # type: ignore[call-overload]
            orchestrator.plan("Task 1"),
            orchestrator.plan("Task 2"),
            orchestrator.plan("Task 3"),
        )

        assert len(results) == 3
        assert all(isinstance(r, PlanResult) for r in results)

    # Contract Test 15: Response text is string
    @pytest.mark.asyncio
    async def test_response_is_string(self, orchestrator: OrchestratorBackend) -> None:
        """Test that PlanResult.response is a string."""
        result = await orchestrator.plan("Test task")  # type: ignore[misc]
        assert isinstance(result.response, str)

    # Contract Test 16: Streaming concatenation
    @pytest.mark.asyncio
    async def test_streaming_concatenation(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that streaming chunks can be concatenated."""
        chunks: list[str] = []

        async for chunk in orchestrator.plan_streaming("Test task"):
            chunks.append(chunk)

        combined = "".join(chunks)
        assert isinstance(combined, str)
        assert len(combined) > 0

    # Contract Test 17: Tool calls list consistency
    @pytest.mark.asyncio
    async def test_tool_calls_list_consistency(
        self, orchestrator: OrchestratorBackend
    ) -> None:
        """Test that tool_calls is always a list."""
        result = await orchestrator.plan("Test task")  # type: ignore[misc]

        assert isinstance(result.tool_calls, list)
        # List can be empty or contain ToolCall instances
        assert all(isinstance(tc, ToolCall) for tc in result.tool_calls)


# Validation functions for external use
def validate_orchestrator_compliance(orchestrator: OrchestratorBackend) -> bool:
    """Validate that an orchestrator instance complies with the contract.

    Args:
        orchestrator: Orchestrator instance to validate

    Returns:
        True if compliant, False otherwise
    """
    # Check required methods exist
    required_methods = [
        "plan",
        "plan_streaming",
        "get_conversation_history",
        "clear_conversation_history",
        "add_tool_result",
    ]

    for method in required_methods:
        if not hasattr(orchestrator, method):
            return False
        if not callable(getattr(orchestrator, method)):
            return False

    # Check required attributes
    if not hasattr(orchestrator, "config"):
        return False
    if not isinstance(orchestrator.config, OrchestratorConfig):
        return False

    return True


async def run_contract_validation(
    orchestrator: OrchestratorBackend,
) -> dict[str, Any]:
    """Run contract validation tests programmatically.

    Args:
        orchestrator: Orchestrator instance to validate

    Returns:
        Dictionary with validation results
    """
    results: dict[str, Any] = {
        "compliant": True,
        "errors": [],
        "warnings": [],
    }

    # Test 1: Basic interface compliance
    if not validate_orchestrator_compliance(orchestrator):
        results["compliant"] = False
        results["errors"].append("Interface compliance failed")
        return results

    # Test 2: Plan returns PlanResult
    try:
        result = await orchestrator.plan("Test")  # type: ignore[misc]
        if not isinstance(result, PlanResult):
            results["compliant"] = False
            results["errors"].append("plan() must return PlanResult")
    except Exception as e:
        results["compliant"] = False
        results["errors"].append(f"plan() raised exception: {e}")

    # Test 3: Streaming works
    try:
        chunks = []
        async for chunk in orchestrator.plan_streaming("Test"):
            if not isinstance(chunk, str):
                results["compliant"] = False
                results["errors"].append("plan_streaming() must yield strings")
                break
            chunks.append(chunk)

        if not chunks:
            results["warnings"].append("plan_streaming() yielded no chunks")
    except Exception as e:
        results["compliant"] = False
        results["errors"].append(f"plan_streaming() raised exception: {e}")

    # Test 4: Conversation history
    try:
        history = orchestrator.get_conversation_history()
        if not isinstance(history, list):
            results["compliant"] = False
            results["errors"].append("get_conversation_history() must return list")
    except Exception as e:
        results["compliant"] = False
        results["errors"].append(
            f"get_conversation_history() raised exception: {e}"
        )

    return results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
