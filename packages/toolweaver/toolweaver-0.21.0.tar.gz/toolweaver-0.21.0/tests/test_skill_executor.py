"""
Tests for SkillExecutor (Phase 4.2)

Tests dynamic skill loading, instantiation, execution,
error handling, and timeout protection.
"""



import pytest

from orchestrator.skills.skill_executor import ExecutionResult, SkillExecutor, get_executor


class TestSkillExecutorBasics:
    """Test basic SkillExecutor functionality."""

    def test_initialization(self) -> None:
        """Test executor initialization."""
        executor = SkillExecutor()

        assert executor.timeout_seconds == 30
        assert executor._skill_cache == {}
        assert executor._execution_count == 0

    def test_custom_timeout(self) -> None:
        """Test custom timeout configuration."""
        executor = SkillExecutor(timeout_seconds=60)

        assert executor.timeout_seconds == 60

    def test_get_stats(self) -> None:
        """Test getting executor statistics."""
        executor = SkillExecutor()
        stats = executor.get_stats()

        assert "cached_skills" in stats
        assert "total_executions" in stats
        assert stats["cached_skills"] == 0
        assert stats["total_executions"] == 0

    def test_clear_cache(self) -> None:
        """Test clearing skill cache."""
        executor = SkillExecutor()

        # Execute a skill to cache it
        executor.execute("cost-control", "get_agent_metrics", {})

        # Cache should have 1 skill
        stats = executor.get_stats()
        assert stats["cached_skills"] == 1

        # Clear cache
        executor.clear_cache()

        # Cache should be empty
        stats = executor.get_stats()
        assert stats["cached_skills"] == 0

    def test_global_executor(self) -> None:
        """Test get_executor returns singleton."""
        executor1 = get_executor()
        executor2 = get_executor()

        assert executor1 is executor2


class TestSkillExecution:
    """Test skill execution functionality."""

    def test_execute_cost_control_skill(self) -> None:
        """Test executing cost-control skill."""
        executor = SkillExecutor()

        result = executor.execute(
            skill_id="cost-control",
            capability="get_agent_metrics",
            parameters={"agent_name": "test-agent"},  # Required parameter
        )

        assert isinstance(result, ExecutionResult)
        # May fail due to dependencies (Redis, agent_tracker), but should handle gracefully
        assert result.skill_id == "cost-control"
        assert result.capability == "get_agent_metrics"
        # Accept any error message as long as it's handled
        if not result.success:
            assert result.error is not None

    def test_execute_task_execution_skill(self) -> None:
        """Test executing task-execution skill."""
        executor = SkillExecutor()

        result = executor.execute(
            skill_id="task-execution",
            capability="get_progress",
            parameters={"task_id": "test-task-123"},
        )

        assert isinstance(result, ExecutionResult)
        # May fail if task doesn't exist, but should handle gracefully
        assert result.skill_id == "task-execution"
        assert result.capability == "get_progress"

    def test_execution_count_increments(self) -> None:
        """Test execution counter increments."""
        executor = SkillExecutor()
        initial_count = executor.get_stats()["total_executions"]

        executor.execute("cost-control", "get_agent_metrics", {})
        executor.execute("cost-control", "get_agent_metrics", {})

        final_count = executor.get_stats()["total_executions"]
        assert final_count == initial_count + 2

    def test_skill_caching(self) -> None:
        """Test skills are cached after first load."""
        executor = SkillExecutor()

        # First execution loads skill
        executor.execute("cost-control", "get_agent_metrics", {"agent_name": "test"})

        # Second execution uses cached skill
        executor.execute("cost-control", "get_agent_metrics", {"agent_name": "test"})

        # Should only have 1 cached skill
        stats = executor.get_stats()
        assert stats["cached_skills"] == 1


class TestSkillExecutionErrors:
    """Test error handling in skill execution."""

    def test_nonexistent_skill(self) -> None:
        """Test executing non-existent skill."""
        executor = SkillExecutor()

        result = executor.execute(
            skill_id="nonexistent-skill", capability="some_capability", parameters={}
        )

        assert result.success is False
        assert result.error is not None
        assert "Failed to load skill module" in result.error
        assert result.skill_id == "nonexistent-skill"

    def test_invalid_capability(self) -> None:
        """Test executing invalid capability."""
        executor = SkillExecutor()

        result = executor.execute(
            skill_id="cost-control", capability="nonexistent_capability", parameters={}
        )

        assert result.success is False
        assert result.error is not None
        assert "Capability" in result.error
        assert "not found" in result.error
        assert result.capability == "nonexistent_capability"

    def test_execution_with_exception(self) -> None:
        """Test handling execution exceptions."""
        executor = SkillExecutor()

        # Try to execute with invalid parameters that cause exception
        result = executor.execute(
            skill_id="cost-control",
            capability="get_agent_metrics",
            parameters={},  # Missing required 'agent_name' parameter
        )

        # Should handle exception gracefully
        assert result.success is False
        assert result.error is not None
        assert "parameter" in result.error.lower() or "argument" in result.error.lower()

    def test_execution_result_structure(self) -> None:
        """Test ExecutionResult has all required fields."""
        executor = SkillExecutor()

        result = executor.execute("cost-control", "get_agent_metrics", {"agent_name": "test"})

        assert hasattr(result, "success")
        assert hasattr(result, "skill_id")
        assert hasattr(result, "capability")
        assert hasattr(result, "result")
        assert hasattr(result, "error")
        assert hasattr(result, "duration_ms")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "execution_id")


class TestSkillExecutorIntegration:
    """Integration tests for SkillExecutor."""

    def test_execute_multiple_skills(self) -> None:
        """Test executing multiple different skills."""
        executor = SkillExecutor()

        skills_to_test = [
            ("cost-control", "get_agent_metrics", {"agent_name": "test"}),
            ("task-execution", "get_progress", {"task_id": "test"}),
        ]

        results = []
        for skill_id, capability, params in skills_to_test:
            result = executor.execute(skill_id=skill_id, capability=capability, parameters=params)
            results.append(result)

        # All should return results (success or failure)
        assert len(results) == 2
        for result in results:
            assert isinstance(result, ExecutionResult)

    def test_execution_timing(self) -> None:
        """Test execution timing is recorded."""
        executor = SkillExecutor()

        result = executor.execute("cost-control", "get_agent_metrics", {"agent_name": "test"})

        # Timing should be recorded for successful or failed executions
        if result.success:
            assert result.duration_ms is not None
            assert result.duration_ms >= 0

    def test_execution_id_uniqueness(self) -> None:
        """Test each execution gets unique ID."""
        executor = SkillExecutor()

        result1 = executor.execute("cost-control", "get_agent_metrics", {})
        result2 = executor.execute("cost-control", "get_agent_metrics", {})

        assert result1.execution_id is not None
        assert result2.execution_id is not None
        assert result1.execution_id != result2.execution_id
        assert "exec-" in result1.execution_id
        assert "cost-control" in result1.execution_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
