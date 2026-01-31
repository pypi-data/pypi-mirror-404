"""
Tests for the Orchestration Engine.

Verifies core orchestration functionality:
- Single and sequential task execution
- State management and persistence
- Error handling and recovery
- Parameter resolution and dependencies
- Observability and metrics
"""

from typing import Any
from unittest.mock import patch

import pytest

from orchestrator._internal.orchestration import (
    DependencyNotMetError,
    ErrorHandler,
    ErrorRecoveryStrategy,
    ExecutionTracker,
    OrchestrationFailedError,
    Orchestrator,
    StateManager,
    Task,
)


class TestTaskModel:
    """Tests for Task class."""

    def test_task_creation(self) -> None:
        """Test creating a task."""
        task = Task(name="extract", tool_name="extract_data", params={"input": "data"})
        assert task.name == "extract"
        assert task.tool_name == "extract_data"
        assert task.params == {"input": "data"}

    def test_task_validation(self) -> None:
        """Test task validation."""
        with pytest.raises(ValueError):
            Task(name="", tool_name="tool")

        with pytest.raises(ValueError):
            Task(name="task", tool_name="")

        with pytest.raises(ValueError):
            Task(name="task", tool_name="tool", retry_count=-1)

        with pytest.raises(ValueError):
            Task(name="task", tool_name="tool", timeout=-1)

    def test_task_param_references(self) -> None:
        """Test detecting parameter references."""
        task = Task(
            name="validate",
            tool_name="validate_data",
            params={"input": "@extract"},
        )
        assert task.has_param_reference()

        deps = task.get_dependencies_from_params()
        assert "extract" in deps

    def test_task_no_references(self) -> None:
        """Test task without references."""
        task = Task(
            name="task",
            tool_name="tool",
            params={"input": "literal_data"},
        )
        assert not task.has_param_reference()

    def test_task_default_values(self) -> None:
        """Test task defaults."""
        task = Task(name="task", tool_name="tool")
        assert task.params == {}
        assert task.depends_on == []
        assert task.retry_count == 3
        assert task.timeout == 30.0


class TestStateManager:
    """Tests for StateManager class."""

    def test_save_and_load_state(self) -> None:
        """Test saving and loading state."""
        state_manager = StateManager()

        data = {"result": "success"}
        state_manager.save_state("task1", data, persist=False)

        loaded = state_manager.load_state("task1")
        assert loaded == data

    def test_state_not_found(self) -> None:
        """Test loading non-existent state."""
        state_manager = StateManager()

        with pytest.raises(KeyError):
            state_manager.load_state("nonexistent")

    def test_has_state(self) -> None:
        """Test checking state existence."""
        state_manager = StateManager()
        assert not state_manager.has_state("task1")

        state_manager.save_state("task1", {"data": "value"}, persist=False)
        assert state_manager.has_state("task1")

    def test_resolve_params_no_references(self) -> None:
        """Test resolving params without references."""
        state_manager = StateManager()
        task = Task(
            name="task",
            tool_name="tool",
            params={"input": "literal", "count": 5},
        )

        resolved = state_manager.resolve_params(task, {})
        assert resolved == {"input": "literal", "count": 5}

    def test_resolve_params_with_references(self) -> None:
        """Test resolving params with task references."""
        state_manager = StateManager()
        state = {"task1": {"value": 10}}

        task = Task(
            name="task2",
            tool_name="tool2",
            params={"input": "@task1", "multiplier": 2},
        )

        resolved = state_manager.resolve_params(task, state)
        assert resolved == {"input": {"value": 10}, "multiplier": 2}

    def test_resolve_params_missing_reference(self) -> None:
        """Test error when referenced task not in state."""
        state_manager = StateManager()
        task = Task(
            name="task2",
            tool_name="tool2",
            params={"input": "@missing_task"},
        )

        with pytest.raises(ValueError):
            state_manager.resolve_params(task, {})

    def test_get_execution_state(self) -> None:
        """Test getting full execution state."""
        state_manager = StateManager()
        state_manager.save_state("task1", {"a": 1}, persist=False)
        state_manager.save_state("task2", {"b": 2}, persist=False)

        state = state_manager.get_execution_state()
        assert "task1" in state
        assert "task2" in state
        assert state["task1"] == {"a": 1}
        assert state["task2"] == {"b": 2}


class TestErrorHandler:
    """Tests for ErrorHandler class."""

    def test_error_handler_creation(self) -> None:
        """Test creating error handler."""
        handler = ErrorHandler(ErrorRecoveryStrategy.FAIL_FAST)
        assert handler.default_strategy == ErrorRecoveryStrategy.FAIL_FAST

    def test_handle_error_fail_fast(self) -> None:
        """Test fail-fast strategy."""
        handler = ErrorHandler(ErrorRecoveryStrategy.FAIL_FAST)
        error = Exception("Test error")

        action = handler.handle_error("task1", "tool1", error, 3)
        assert action == "stop"

    def test_handle_error_retry(self) -> None:
        """Test retry strategy."""
        handler = ErrorHandler(ErrorRecoveryStrategy.RETRY)
        error = Exception("Test error")

        # First attempt fails, but retries remain
        action = handler.handle_error("task1", "tool1", error, 2)
        assert action == "retry"

        # All retries exhausted
        action = handler.handle_error("task1", "tool1", error, 0)
        assert action == "stop"

    def test_handle_error_skip(self) -> None:
        """Test skip strategy."""
        handler = ErrorHandler(ErrorRecoveryStrategy.SKIP)
        error = Exception("Test error")

        action = handler.handle_error("task1", "tool1", error, 3)
        assert action == "skip"

    def test_error_tracking(self) -> None:
        """Test tracking errors."""
        handler = ErrorHandler()
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")

        handler.add_error(error1)
        handler.add_error(error2)

        errors = handler.get_errors()
        assert len(errors) == 2

    def test_error_clearing(self) -> None:
        """Test clearing errors."""
        handler = ErrorHandler()
        handler.add_error(Exception("Error"))

        handler.clear_errors()
        assert len(handler.get_errors()) == 0


class TestExecutionTracker:
    """Tests for ExecutionTracker class."""

    def test_tracker_creation(self) -> None:
        """Test creating execution tracker."""
        tracker = ExecutionTracker("exec123")
        assert tracker.execution_id == "exec123"

    def test_track_task_execution(self) -> None:
        """Test tracking task execution."""
        tracker = ExecutionTracker("exec123")

        metrics = tracker.start_task("task1", "tool1")
        assert metrics.task_name == "task1"
        assert metrics.tool_name == "tool1"
        assert metrics.status == "running"

        tracker.complete_task("task1", "success")
        metrics = tracker.metrics.task_metrics["task1"]
        assert metrics.status == "success"

    def test_get_metrics(self) -> None:
        """Test retrieving metrics."""
        tracker = ExecutionTracker("exec123")
        tracker.start_task("task1", "tool1")
        tracker.complete_task("task1", "success")

        metrics = tracker.get_metrics()
        assert metrics.execution_id == "exec123"
        assert len(metrics.task_metrics) == 1

    def test_orchestration_metrics(self) -> None:
        """Test orchestration-level metrics."""
        tracker = ExecutionTracker("exec123")

        tracker.start_task("task1", "tool1")
        tracker.complete_task("task1", "success")

        tracker.start_task("task2", "tool2")
        tracker.complete_task("task2", "success")

        metrics = tracker.complete_orchestration()
        assert metrics.total_tasks == 2
        assert metrics.succeeded_tasks == 2
        assert metrics.success_rate() == 1.0


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_orchestrator_creation(self) -> None:
        """Test creating orchestrator."""
        orchestrator = Orchestrator()
        assert orchestrator is not None

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_execute_single_task(self, mock_execute: Any) -> None:
        """Test executing a single task."""
        mock_execute.return_value = {"result": "success"}

        orchestrator = Orchestrator()
        tasks = [Task(name="task1", tool_name="tool1", params={"input": "data"})]

        result = orchestrator.execute(tasks)

        assert result.success
        assert "task1" in result.task_outputs
        assert result.final_output == {"result": "success"}

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_execute_task_sequence(self, mock_execute: Any) -> None:
        """Test executing task sequence."""
        mock_execute.side_effect = [
            {"value": 10},  # task1 output
            {"value": 20},  # task2 output
            {"value": 30},  # task3 output
        ]

        orchestrator = Orchestrator()
        tasks = [
            Task(name="task1", tool_name="tool1", params={"input": "a"}),
            Task(name="task2", tool_name="tool2", params={"input": "@task1"}),
            Task(name="task3", tool_name="tool3", params={"input": "@task2"}),
        ]

        result = orchestrator.execute(tasks)

        assert result.success
        assert len(result.task_outputs) == 3
        assert result.final_output == {"value": 30}

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_parameter_resolution(self, mock_execute: Any) -> None:
        """Test parameter resolution between tasks."""

        def check_params(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            # task2 should receive task1's output as input
            if tool_name == "tool2":
                assert params["input"] == {"value": 10}
            return {"result": "ok"}

        mock_execute.side_effect = [{"value": 10}, check_params]

        orchestrator = Orchestrator()
        tasks = [
            Task(name="task1", tool_name="tool1", params={"input": "data"}),
            Task(name="task2", tool_name="tool2", params={"input": "@task1"}),
        ]

        result = orchestrator.execute(tasks)
        assert result.success

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_task_retry(self, mock_execute: Any) -> None:
        """Test task retry on failure."""
        # First attempt fails, second succeeds
        mock_execute.side_effect = [
            Exception("Temporary error"),
            {"result": "success"},
        ]

        orchestrator = Orchestrator()
        tasks = [Task(name="task1", tool_name="tool1", params={}, retry_count=1)]

        result = orchestrator.execute(tasks)

        # Should succeed after retry
        assert result.success
        assert mock_execute.call_count == 2

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_task_failure_fail_fast(self, mock_execute: Any) -> None:
        """Test fail-fast on task failure."""
        mock_execute.side_effect = Exception("Tool error")

        orchestrator = Orchestrator()
        tasks = [Task(name="task1", tool_name="tool1", params={}, retry_count=0)]

        with pytest.raises(OrchestrationFailedError):
            orchestrator.execute(tasks, recovery_strategy=ErrorRecoveryStrategy.FAIL_FAST)

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_task_failure_skip(self, mock_execute: Any) -> None:
        """Test skip strategy on task failure."""
        mock_execute.side_effect = [
            Exception("Tool error"),  # task1 fails
            {"result": "ok"},  # task2 succeeds
        ]

        orchestrator = Orchestrator()
        tasks = [
            Task(name="task1", tool_name="tool1", params={}, retry_count=0),
            Task(name="task2", tool_name="tool2", params={"input": "data"}, retry_count=0),
        ]

        result = orchestrator.execute(tasks, recovery_strategy=ErrorRecoveryStrategy.SKIP)

        # Should succeed despite task1 failure
        assert result.success
        assert "task1" not in result.task_outputs  # Skipped
        assert "task2" in result.task_outputs

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_dependency_check(self, mock_execute: Any) -> None:
        """Test dependency checking."""
        mock_execute.return_value = {"result": "ok"}

        orchestrator = Orchestrator()
        tasks = [
            Task(
                name="task2",
                tool_name="tool2",
                params={"input": "@task1"},  # Depends on task1
            ),
            Task(name="task1", tool_name="tool1", params={}),  # task1 not yet executed
        ]

        with pytest.raises(DependencyNotMetError):
            orchestrator.execute(tasks)

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_empty_orchestration(self, mock_execute: Any) -> None:
        """Test orchestration with no tasks."""
        orchestrator = Orchestrator()
        result = orchestrator.execute([])

        assert result.success
        assert len(result.task_outputs) == 0

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_task_with_transform(self, mock_execute: Any) -> None:
        """Test task with output transformation."""
        mock_execute.return_value = [1, 2, 3]

        def transform_output(output: list[int]) -> dict[str, int]:
            return {"sum": sum(output)}

        orchestrator = Orchestrator()
        tasks = [
            Task(
                name="task1",
                tool_name="tool1",
                params={},
                transform=transform_output,
            )
        ]

        result = orchestrator.execute(tasks)

        assert result.final_output == {"sum": 6}

    @patch("orchestrator._internal.orchestration.Orchestrator._execute_tool")
    def test_execution_metrics(self, mock_execute: Any) -> None:
        """Test execution metrics collection."""
        mock_execute.return_value = {"result": "ok"}

        orchestrator = Orchestrator()
        tasks = [
            Task(name="task1", tool_name="tool1", params={}),
            Task(name="task2", tool_name="tool2", params={}),
        ]

        result = orchestrator.execute(tasks)

        assert "metrics" in result.metadata
        metrics = result.metadata["metrics"]
        assert metrics["total_tasks"] == 2
        assert metrics["succeeded_tasks"] == 2
        assert metrics["success_rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
