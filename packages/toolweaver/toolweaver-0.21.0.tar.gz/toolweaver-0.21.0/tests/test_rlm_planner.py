"""
Comprehensive test suite for RLM Planner integration.

Tests:
- RLM decision logic (should_use_rlm)
- Traditional plan generation
- RLM plan generation with strategies (peek, grep, partition, programmatic)
- Plan structure validation (JSON serialization, step dependencies)
- Step execution for each tool type
- Planner selection logic
"""

import json
import os
from typing import Any

import pytest

from orchestrator.skills.task_planning.rlm_planner import (
    execute_rlm_plan_step,
    generate_rlm_plan,
    generate_traditional_plan,
    select_planner,
    should_use_rlm,
)
from orchestrator.tools.repl_environment import REPLEnvironment

# ===== Fixtures =====


@pytest.fixture
def simple_task() -> Any:
    """Simple, straightforward task."""
    return "Explain what this code does"


@pytest.fixture
def complex_task() -> Any:
    """Complex task requiring decomposition."""
    return "Analyze all functions in this codebase, categorize by performance complexity, and suggest optimizations for the bottom 10%"


@pytest.fixture
def small_context() -> Any:
    """Small context (~10KB)."""
    return "x" * 10_000


@pytest.fixture
def large_context() -> Any:
    """Large context (~600KB, exceeds RLM thresholds)."""
    return "x" * 600_000


@pytest.fixture
def dict_context() -> Any:
    """Dictionary-based context (structured data)."""
    return {
        "code": "def foo():\n    return 42",
        "metadata": {"lines": 2, "type": "function"},
        "nested": {"description": "A simple function", "tags": ["test", "simple"]},
    }


@pytest.fixture
def repl_env() -> Any:
    """REPL environment for step execution."""
    # Use string context for partition/grep tests
    context = "line1 important\nline2 data\nline3 important\nline4 other\nline5 important\n" * 100
    env = REPLEnvironment(context)
    return env


# ===== Test Classes =====


class TestShouldUseRLM:
    """Tests for RLM decision logic."""

    def test_simple_task_small_context_uses_traditional(self, simple_task: Any, small_context: Any) -> None:
        """Simple tasks with small context should use traditional."""
        use_rlm, reason = should_use_rlm(simple_task, small_context)
        assert use_rlm is False
        assert "simple" in reason.lower() or "small" in reason.lower()

    def test_complex_task_large_context_uses_rlm(self, complex_task: Any, large_context: Any) -> None:
        """Complex tasks with large context should use RLM."""
        use_rlm, reason = should_use_rlm(complex_task, large_context)
        assert use_rlm is True
        assert "complex" in reason.lower() or "large" in reason.lower()

    def test_rlm_mode_env_variable_always(self) -> None:
        """RLM_MODE=always should always enable RLM."""
        os.environ["RLM_MODE"] = "always"
        try:
            use_rlm, reason = should_use_rlm("any task", "any context")
            assert use_rlm is True
        finally:
            os.environ.pop("RLM_MODE", None)

    def test_rlm_mode_env_variable_off(self) -> None:
        """RLM_MODE=off should always disable RLM."""
        os.environ["RLM_MODE"] = "off"
        try:
            use_rlm, reason = should_use_rlm("complex task", "x" * 500_000)
            assert use_rlm is False
        finally:
            os.environ.pop("RLM_MODE", None)

    def test_decision_returns_tuple(self, simple_task: Any, small_context: Any) -> None:
        """Decision should return (bool, str) tuple."""
        result = should_use_rlm(simple_task, small_context)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_dict_context_handled(self, complex_task: Any, dict_context: Any) -> None:
        """Should handle dict context (converts to JSON)."""
        use_rlm, reason = should_use_rlm(complex_task, dict_context)
        assert isinstance(use_rlm, bool)
        assert reason


class TestGenerateTraditionalPlan:
    """Tests for traditional plan generation."""

    def test_traditional_plan_structure(self, simple_task: Any, small_context: Any) -> None:
        """Traditional plan should have expected structure."""
        plan = generate_traditional_plan(simple_task, small_context)

        assert plan["strategy"] == "traditional"
        assert plan["task"] == simple_task
        assert "context_size_bytes" in plan
        assert "steps" in plan
        assert "execution_order" in plan
        assert "estimated_recursion_depth" in plan

    def test_traditional_plan_single_step(self, simple_task: Any, small_context: Any) -> None:
        """Traditional plan should have exactly 1 step."""
        plan = generate_traditional_plan(simple_task, small_context)
        assert len(plan["steps"]) == 1
        assert plan["steps"][0]["id"] == 1
        assert plan["steps"][0]["tool"] == "direct_llm_call"

    def test_traditional_plan_step_has_task(self, simple_task: Any, small_context: Any) -> None:
        """Traditional step should include task in params."""
        plan = generate_traditional_plan(simple_task, small_context)
        step = plan["steps"][0]
        assert "params" in step
        assert step["params"]["task"] == simple_task

    def test_traditional_plan_context_truncated(self, simple_task: Any, large_context: Any) -> None:
        """Traditional plan should truncate context for safety."""
        plan = generate_traditional_plan(simple_task, large_context)
        step = plan["steps"][0]
        context_in_params = step["params"]["context"]
        assert len(context_in_params) <= 10000

    def test_traditional_plan_recursion_depth_zero(self, simple_task: Any, small_context: Any) -> None:
        """Traditional plan should have recursion depth = 0."""
        plan = generate_traditional_plan(simple_task, small_context)
        assert plan["estimated_recursion_depth"] == 0

    def test_traditional_plan_with_dict_context(self, simple_task: Any, dict_context: Any) -> None:
        """Traditional plan should handle dict context."""
        plan = generate_traditional_plan(simple_task, dict_context)
        assert plan["context_size_bytes"] > 0
        assert isinstance(plan["context_size_bytes"], int)

    def test_traditional_plan_json_serializable(self, simple_task: Any, small_context: Any) -> None:
        """Traditional plan should be JSON serializable."""
        plan = generate_traditional_plan(simple_task, small_context)
        json_str = json.dumps(plan)
        assert isinstance(json_str, str)
        deserialized = json.loads(json_str)
        assert deserialized["strategy"] == "traditional"


class TestGenerateRLMPlan:
    """Tests for RLM plan generation."""

    def test_rlm_plan_structure(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan should have expected structure."""
        plan = generate_rlm_plan(complex_task, large_context)

        assert plan["strategy"] == "rlm"
        assert plan["task"] == complex_task
        assert "context_size_bytes" in plan
        assert "estimated_tokens" in plan
        assert "task_complexity" in plan
        assert "rlm_strategy" in plan
        assert "estimated_recursion_depth" in plan
        assert "steps" in plan
        assert "execution_order" in plan

    def test_rlm_plan_starts_with_peek(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan should always start with peek step."""
        plan = generate_rlm_plan(complex_task, large_context)
        assert len(plan["steps"]) >= 2
        first_step = plan["steps"][0]
        assert first_step["tool"] == "rlm_peek"
        assert first_step["id"] == 1

    def test_rlm_plan_grep_strategy(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan with grep strategy should have grep step."""
        plan = generate_rlm_plan(complex_task, large_context, strategy_hint="grep")

        # Should have peek + grep
        tools = [step["tool"] for step in plan["steps"]]
        assert "rlm_peek" in tools
        assert "rlm_grep" in tools
        assert plan["rlm_strategy"] == "grep"

    def test_rlm_plan_partition_strategy_has_recursion(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan with partition should have recursion steps."""
        plan = generate_rlm_plan(complex_task, large_context, strategy_hint="partition")

        tools = [step["tool"] for step in plan["steps"]]
        assert "rlm_peek" in tools
        assert "rlm_partition" in tools
        assert "recursive_llm_call" in tools
        assert "aggregate_results" in tools
        assert plan["estimated_recursion_depth"] > 0

    def test_rlm_plan_programmatic_strategy(self, complex_task: Any, small_context: Any) -> None:
        """RLM plan with programmatic strategy should have programmatic step."""
        plan = generate_rlm_plan(complex_task, small_context, strategy_hint="programmatic")

        tools = [step["tool"] for step in plan["steps"]]
        assert "rlm_peek" in tools
        assert "rlm_programmatic" in tools
        assert plan["rlm_strategy"] == "programmatic"

    def test_rlm_plan_dependencies_valid(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan steps should have valid dependencies."""
        plan = generate_rlm_plan(complex_task, large_context)
        step_ids = {step["id"] for step in plan["steps"]}

        for step in plan["steps"]:
            if "depends_on" in step:
                for dep_id in step["depends_on"]:
                    assert dep_id in step_ids, f"Dependency {dep_id} not found in steps"

    def test_rlm_plan_execution_order_valid(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan execution order should reference valid step IDs."""
        plan = generate_rlm_plan(complex_task, large_context)
        step_ids = {step["id"] for step in plan["steps"]}

        for order_group in plan["execution_order"]:
            for step_id in order_group:
                assert step_id in step_ids

    def test_rlm_plan_with_dict_context(self, complex_task: Any, dict_context: Any) -> None:
        """RLM plan should handle dict context."""
        plan = generate_rlm_plan(complex_task, dict_context)
        assert plan["context_size_bytes"] > 0
        assert "steps" in plan

    def test_rlm_plan_chunk_size_reasonable(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan should have reasonable chunk size."""
        plan = generate_rlm_plan(complex_task, large_context, strategy_hint="partition")

        partition_step = next((s for s in plan["steps"] if s["tool"] == "rlm_partition"), None)
        assert partition_step is not None
        chunk_size = partition_step["params"]["chunk_size"]
        # Chunk size should be reasonable (at least 10KB)
        assert chunk_size >= 10_000

    def test_rlm_plan_json_serializable(self, complex_task: Any, large_context: Any) -> None:
        """RLM plan should be JSON serializable."""
        plan = generate_rlm_plan(complex_task, large_context)
        json_str = json.dumps(plan)
        assert isinstance(json_str, str)
        deserialized = json.loads(json_str)
        assert deserialized["strategy"] == "rlm"


class TestExecuteRLMPlanStep:
    """Tests for RLM plan step execution."""

    @pytest.mark.asyncio
    async def test_execute_peek_step(self, repl_env: Any) -> None:
        """Should execute peek step successfully."""
        step = {
            "tool": "rlm_peek",
            "params": {"peek_chars": 100},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_grep_step(self, repl_env: Any) -> None:
        """Should execute grep step."""
        step = {
            "tool": "rlm_grep",
            "params": {"pattern": "important"},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_partition_step(self, repl_env: Any) -> None:
        """Should execute partition step."""
        step = {
            "tool": "rlm_partition",
            "params": {"chunk_size": 1000},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "chunks" in result
        assert "count" in result
        assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_execute_recursive_llm_call_step(self, repl_env: Any) -> None:
        """Should execute recursive LLM call step."""
        step = {
            "tool": "recursive_llm_call",
            "params": {"task": "analyze", "context_size": 1000},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "status" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_execute_aggregate_results_step(self, repl_env: Any) -> None:
        """Should execute aggregate results step."""
        step = {
            "tool": "aggregate_results",
            "params": {"sources": ["result1", "result2"]},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert result["aggregated"] is True
        assert len(result["sources"]) == 2

    @pytest.mark.asyncio
    async def test_execute_programmatic_step_with_code(self, repl_env: Any) -> None:
        """Should execute programmatic step with code."""
        step = {
            "tool": "rlm_programmatic",
            "params": {"code": "result = 1 + 1"},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "success" in result
        assert "output" in result

    @pytest.mark.asyncio
    async def test_execute_programmatic_step_without_code(self, repl_env: Any) -> None:
        """Should handle programmatic step without code."""
        step = {
            "tool": "rlm_programmatic",
            "params": {},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_direct_llm_call_step(self, repl_env: Any) -> None:
        """Should execute direct LLM call step."""
        step = {
            "tool": "direct_llm_call",
            "params": {"task": "analyze"},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "status" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_returns_error(self, repl_env: Any) -> None:
        """Should return error for unknown tool."""
        step = {
            "tool": "unknown_tool",
            "params": {},
        }
        result = await execute_rlm_plan_step(step, repl_env, {})
        assert "error" in result
        assert "unknown" in result["error"].lower()


class TestSelectPlanner:
    """Tests for planner selection logic."""

    def test_select_planner_returns_string(self, simple_task: Any, small_context: Any) -> None:
        """Should return string indicating planner type."""
        planner = select_planner(simple_task, small_context)
        assert isinstance(planner, str)
        assert planner in ["traditional", "rlm"]

    def test_select_planner_simple_task_traditional(self, simple_task: Any, small_context: Any) -> None:
        """Simple task with small context should select traditional."""
        planner = select_planner(simple_task, small_context)
        assert planner == "traditional"

    def test_select_planner_complex_task_rlm(self, complex_task: Any, large_context: Any) -> None:
        """Complex task with large context should select RLM."""
        planner = select_planner(complex_task, large_context)
        assert planner == "rlm"

    def test_select_planner_respects_env_variable(self) -> None:
        """Planner selection should respect RLM_MODE environment variable."""
        os.environ["RLM_MODE"] = "always"
        try:
            planner = select_planner("any", "any")
            assert planner == "rlm"
        finally:
            os.environ.pop("RLM_MODE", None)


class TestPlanGeneration:
    """Integration tests for plan generation workflow."""

    def test_plan_generation_workflow_simple(self, simple_task: Any, small_context: Any) -> None:
        """Should generate complete traditional plan."""
        plan = generate_traditional_plan(simple_task, small_context)
        assert plan["strategy"] == "traditional"
        assert all(key in plan for key in ["task", "steps", "execution_order"])

    def test_plan_generation_workflow_complex(self, complex_task: Any, large_context: Any) -> None:
        """Should generate complete RLM plan."""
        plan = generate_rlm_plan(complex_task, large_context)
        assert plan["strategy"] == "rlm"
        assert all(
            key in plan
            for key in [
                "task",
                "steps",
                "execution_order",
                "estimated_recursion_depth",
                "rlm_strategy",
            ]
        )

    def test_plans_have_consistent_step_ids(self, complex_task: Any, large_context: Any) -> None:
        """Steps should have sequential IDs starting from 1."""
        plan = generate_rlm_plan(complex_task, large_context)
        step_ids = [step["id"] for step in plan["steps"]]
        assert step_ids == list(range(1, len(step_ids) + 1))

    def test_plans_have_descriptions(self, complex_task: Any, large_context: Any) -> None:
        """All steps should have descriptions."""
        plan = generate_rlm_plan(complex_task, large_context)
        for step in plan["steps"]:
            assert "description" in step
            assert isinstance(step["description"], str)
            assert len(step["description"]) > 0

    def test_traditional_and_rlm_produce_different_plans(self, complex_task: Any, large_context: Any) -> None:
        """Traditional and RLM plans should differ significantly."""
        trad_plan = generate_traditional_plan(complex_task, large_context)
        rlm_plan = generate_rlm_plan(complex_task, large_context)

        assert trad_plan["strategy"] != rlm_plan["strategy"]
        assert len(trad_plan["steps"]) < len(rlm_plan["steps"])


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_task_string(self) -> None:
        """Should handle empty task string."""
        plan = generate_traditional_plan("", "context")
        assert plan["task"] == ""
        assert "steps" in plan

    def test_empty_context_string(self) -> None:
        """Should handle empty context string."""
        plan = generate_traditional_plan("task", "")
        assert plan["context_size_bytes"] == 0

    def test_very_large_context(self) -> None:
        """Should handle very large context gracefully."""
        huge_context = "x" * 10_000_000  # 10MB
        plan = generate_traditional_plan("task", huge_context)
        assert plan["context_size_bytes"] > 0

    def test_special_characters_in_task(self) -> None:
        """Should handle special characters in task."""
        task = "Task with special chars: @#$%^&*()"
        plan = generate_traditional_plan(task, "context")
        assert plan["task"] == task

    def test_unicode_in_context(self) -> None:
        """Should handle unicode characters in context."""
        context = "Unicode test: 你好世界 🚀"
        plan = generate_traditional_plan("task", context)
        assert "context_size_bytes" in plan

    def test_nested_dict_context(self) -> None:
        """Should handle deeply nested dict context."""
        nested = {"a": {"b": {"c": {"d": "value"}}}}
        plan = generate_traditional_plan("task", nested)
        assert "context_size_bytes" in plan
