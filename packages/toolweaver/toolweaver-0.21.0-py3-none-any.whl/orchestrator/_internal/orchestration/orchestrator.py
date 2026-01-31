"""
Core orchestration engine for executing tool sequences.

Main Orchestrator class that coordinates execution of multiple tools
with state management, error handling, and observability.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any

from .error_handler import (
    DependencyNotMetError,
    ErrorHandler,
    ErrorRecoveryStrategy,
    OrchestrationFailedError,
    ParameterResolutionError,
    TaskExecutionError,
)
from .execution_tracker import ExecutionTracker
from .state_manager import StateManager
from .task import Task


@dataclass
class OrchestrationResult:
    """Result of an orchestration execution."""

    execution_id: str
    final_output: Any = None
    task_outputs: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    success: bool = False
    errors: list[Exception] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    task_metrics: dict[str, Any] | None = None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OrchestrationResult(execution_id={self.execution_id}, "
            f"success={self.success}, tasks={len(self.task_outputs)}, "
            f"time={self.execution_time:.2f}s)"
        )


class Orchestrator:
    """
    Execute sequences of tools with state management and observability.

    Coordinates multi-step tool executions with:
    - Sequential task execution
    - Parameter passing between tasks
    - State persistence via StorageBackend (Phase -1)
    - Error handling and recovery
    - Execution metrics via ObservabilityBackend (Phase -1)
    - Permission checking via AuthProvider (Phase -1)
    """

    def __init__(
        self,
        storage_backend: Any = None,
        observability_backend: Any = None,
        auth_provider: Any = None,
        tool_registry: Any = None,
    ) -> None:
        """
        Initialize Orchestrator with Phase -1 systems.

        Args:
            storage_backend: Phase -1 StorageBackend for state persistence
            observability_backend: Phase -1 ObservabilityBackend for logging
            auth_provider: Phase -1 AuthProvider for permission checking
            tool_registry: Phase 0 ToolRegistry for tool discovery
        """
        self.storage = storage_backend
        self.observability = observability_backend
        self.auth = auth_provider
        self.registry = tool_registry

        # Import defaults if not provided
        if self.storage is None:
            try:
                self.storage = None  # Factory not yet implemented
            except Exception:
                pass

        if self.observability is None:
            try:
                self.observability = None  # Factory not yet implemented
            except Exception:
                pass

        if self.registry is None:
            try:
                from ..backends.tools import get_tool_registry

                self.registry = get_tool_registry()
            except Exception:
                pass

    def execute(
        self,
        tasks: list[Task],
        recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.FAIL_FAST,
        persist_state: bool = True,
    ) -> OrchestrationResult:
        """
        Execute a sequence of tasks (orchestration).

        Args:
            tasks: List of Task objects to execute in sequence
            recovery_strategy: How to handle errors (see ErrorRecoveryStrategy)
            persist_state: Whether to persist state to StorageBackend

        Returns:
            OrchestrationResult with outputs, metrics, and status

        Raises:
            OrchestrationFailedError: If orchestration fails
            ValueError: If task configuration is invalid
        """
        execution_id = str(uuid.uuid4())
        state_manager = StateManager(self.storage, execution_id)
        error_handler = ErrorHandler(recovery_strategy)
        tracker = ExecutionTracker(execution_id, self.observability)

        result = OrchestrationResult(execution_id=execution_id)

        if not tasks:
            result.success = True
            return result

        # Validate all tasks first
        self._validate_tasks(tasks)

        # Execute tasks in sequence
        for task in tasks:
            try:
                # Check dependencies
                self._check_dependencies(task, state_manager)

                # Check permissions
                self._check_permissions(task)

                # Resolve parameters
                params = self._resolve_params(task, state_manager)

                # Execute task with retries
                task_result = self._execute_task_with_retry(task, params, error_handler, tracker)

                # Save state
                state_manager.save_state(task.name, task_result, persist=persist_state)

                # Mark task as successful
                tracker.complete_task(task.name, "success")

            except (DependencyNotMetError, ParameterResolutionError):
                # These are validation errors that should propagate immediately
                raise

            except TaskExecutionError as e:
                error_handler.add_error(e)
                tracker.complete_task(task.name, "failed", error=str(e))

                # Decide what to do based on strategy
                action = error_handler.handle_error(
                    task.name,
                    task.tool_name,
                    e,
                    task.retry_count,
                    recovery_strategy,
                )

                if action == "retry":
                    # Retry logic already handled in _execute_task_with_retry
                    continue
                elif action == "skip":
                    # Skip this task and continue
                    tracker.complete_task(task.name, "skipped", error=str(e))
                    continue
                else:
                    # Stop execution
                    result.errors = error_handler.get_errors()
                    metrics = tracker.complete_orchestration()
                    result.metadata["metrics"] = metrics.to_dict()
                    raise OrchestrationFailedError(
                        f"Orchestration failed at task '{task.name}': {e}",
                        errors=result.errors,
                    ) from None

            except Exception as e:
                # Unexpected error
                error_handler.add_error(e)
                tracker.complete_task(task.name, "failed", error=str(e))

                result.errors = error_handler.get_errors()
                metrics = tracker.complete_orchestration()
                result.metadata["metrics"] = metrics.to_dict()

                raise OrchestrationFailedError(
                    f"Unexpected error in task '{task.name}': {e}",
                    errors=result.errors,
                ) from None

        # Get final state
        state = state_manager.get_execution_state()
        result.task_outputs = state
        result.final_output = state.get(tasks[-1].name) if tasks else None
        result.success = True
        result.errors = error_handler.get_errors()

        # Finalize metrics
        metrics = tracker.complete_orchestration()
        result.metadata["metrics"] = metrics.to_dict()
        result.execution_time = metrics.duration_ms / 1000 if metrics.duration_ms else 0

        return result

    def _execute_task_with_retry(
        self,
        task: Task,
        params: dict[str, Any],
        error_handler: ErrorHandler,
        tracker: ExecutionTracker,
    ) -> Any:
        """
        Execute a task with retry logic.

        Args:
            task: Task to execute
            params: Resolved parameters
            error_handler: Error handler for retry decisions
            tracker: Execution tracker

        Returns:
            Task result

        Raises:
            TaskExecutionError: If task fails after all retries
        """
        max_attempts = task.retry_count + 1
        last_error = None

        for attempt in range(1, max_attempts + 1):
            task_metrics = tracker.start_task(task.name, task.tool_name)
            task_metrics.attempt = attempt

            try:
                # Execute tool
                result = self._execute_tool(task.tool_name, params, task.timeout)

                # Transform result if needed
                if task.transform:
                    result = task.transform(result)

                return result

            except Exception as e:
                last_error = e
                task_metrics.error = str(e)

                if attempt < max_attempts:
                    # More retries available, continue
                    continue
                else:
                    # No more retries
                    break

        # All retries exhausted
        raise TaskExecutionError(
            task.name,
            task.tool_name,
            last_error or Exception("Unknown error"),
            attempt=max_attempts,
        )

    def _execute_tool(self, tool_name: str, params: dict[str, Any], timeout: float) -> Any:
        """
        Execute a tool via Phase 0 Week 1 helpers.

        Args:
            tool_name: Name of the tool
            params: Parameters to pass to tool
            timeout: Timeout in seconds

        Returns:
            Tool result

        Raises:
            Exception: If tool execution fails
        """
        try:
            # Use Phase 0 Week 1 helper function
            from ...tools import execute_tool

            return execute_tool(tool_name, params)
        except Exception as e:
            raise Exception(f"Failed to execute tool '{tool_name}': {e}") from None

    def _validate_tasks(self, tasks: list[Task]) -> None:
        """Validate task configuration."""
        task_names = set()

        for task in tasks:
            if task.name in task_names:
                raise ValueError(f"Duplicate task name: {task.name}")
            task_names.add(task.name)

            # Check dependencies exist
            for dep in task.depends_on:
                if dep not in task_names and task != tasks[0]:
                    # Will be checked later when parsing dependencies
                    pass

    def _check_dependencies(self, task: Task, state_manager: StateManager) -> None:
        """
        Check that task dependencies have completed.

        Args:
            task: Task to check
            state_manager: State manager with current state

        Raises:
            DependencyNotMetError: If dependencies not met
        """
        # Explicit dependencies
        for dep in task.depends_on:
            if not state_manager.has_state(dep):
                raise DependencyNotMetError(task.name, dep)

        # Implicit dependencies from parameter references
        deps_from_params = task.get_dependencies_from_params()
        for dep in deps_from_params:
            if not state_manager.has_state(dep):
                raise DependencyNotMetError(task.name, dep)

    def _resolve_params(self, task: Task, state_manager: StateManager) -> dict[str, Any]:
        """
        Resolve task parameters, substituting references to previous tasks.

        Args:
            task: Task with parameters to resolve
            state_manager: State manager with current state

        Returns:
            Resolved parameters

        Raises:
            ParameterResolutionError: If resolution fails
        """
        try:
            state = state_manager.get_execution_state()
            return state_manager.resolve_params(task, state)
        except Exception as e:
            raise ParameterResolutionError(task.name, e) from None

    def _check_permissions(self, task: Task) -> None:
        """
        Check if user has permission to execute task's tool.

        Args:
            task: Task to check

        Raises:
            Exception: If permission denied
        """
        if self.auth:
            try:
                # Optional: Check auth via Phase -1 AuthProvider
                # For now, allow all (auth provider can be plugged in later)
                pass
            except Exception as e:
                raise Exception(f"Permission denied for task '{task.name}': {e}") from None

    def __repr__(self) -> str:
        """String representation."""
        return "Orchestrator(Phase 0 Week 2 - Sequential Tool Orchestration)"
