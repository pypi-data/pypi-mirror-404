"""
Execution tracking and observability for orchestration.

Integrates with Phase -1 ObservabilityBackend to track metrics,
durations, and other execution details.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""

    task_name: str
    tool_name: str
    status: str  # "success", "failed", "skipped", "retry"
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    input_size: int | None = None
    output_size: int | None = None
    error: str | None = None
    attempt: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def finalize(self) -> None:
        """Finalize metrics (calculate duration)."""
        if self.end_time is None:
            self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        self.finalize()
        return {
            "task_name": self.task_name,
            "tool_name": self.tool_name,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "error": self.error,
            "attempt": self.attempt,
            "metadata": self.metadata,
        }


@dataclass
class OrchestrationMetrics:
    """Metrics for entire orchestration."""

    execution_id: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    total_tasks: int = 0
    succeeded_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    total_attempts: int = 0
    task_metrics: dict[str, TaskMetrics] = field(default_factory=dict)
    errors: list[Any] = field(default_factory=list)

    def finalize(self) -> None:
        """Finalize metrics (calculate totals)."""
        if self.end_time is None:
            self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

        # Finalize all task metrics
        for metrics in self.task_metrics.values():
            metrics.finalize()

        # Count statuses
        self.succeeded_tasks = sum(1 for m in self.task_metrics.values() if m.status == "success")
        self.failed_tasks = sum(1 for m in self.task_metrics.values() if m.status == "failed")
        self.skipped_tasks = sum(1 for m in self.task_metrics.values() if m.status == "skipped")

        self.total_tasks = len(self.task_metrics)
        self.total_attempts = sum(m.attempt for m in self.task_metrics.values())

    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        self.finalize()
        if self.total_tasks == 0:
            return 0.0
        return self.succeeded_tasks / self.total_tasks

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        self.finalize()
        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "total_tasks": self.total_tasks,
            "succeeded_tasks": self.succeeded_tasks,
            "failed_tasks": self.failed_tasks,
            "skipped_tasks": self.skipped_tasks,
            "total_attempts": self.total_attempts,
            "success_rate": self.success_rate(),
            "task_metrics": {
                name: metrics.to_dict() for name, metrics in self.task_metrics.items()
            },
        }


class ExecutionTracker:
    """
    Track orchestration execution metrics and logs.

    Integrates with Phase -1 ObservabilityBackend for persistent logging.
    """

    def __init__(self, execution_id: str, observability_backend: Any = None) -> None:
        """
        Initialize ExecutionTracker.

        Args:
            execution_id: Unique ID for this orchestration
            observability_backend: Phase -1 ObservabilityBackend (optional)
        """
        self.execution_id = execution_id
        self.observability = observability_backend
        self.metrics = OrchestrationMetrics(execution_id=execution_id, start_time=time.time())

    def start_task(self, task_name: str, tool_name: str) -> TaskMetrics:
        """
        Start tracking a task execution.

        Args:
            task_name: Name of the task
            tool_name: Name of the tool being executed

        Returns:
            TaskMetrics object to track the task
        """
        task_metrics = TaskMetrics(
            task_name=task_name,
            tool_name=tool_name,
            status="running",
            start_time=time.time(),
        )
        self.metrics.task_metrics[task_name] = task_metrics
        return task_metrics

    def complete_task(
        self,
        task_name: str,
        status: str,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Mark task as complete.

        Args:
            task_name: Name of the task
            status: Task status ("success", "failed", "skipped", "retry")
            error: Error message if failed
            metadata: Additional metadata
        """
        if task_name not in self.metrics.task_metrics:
            return

        task_metrics = self.metrics.task_metrics[task_name]
        task_metrics.end_time = time.time()
        task_metrics.status = status
        task_metrics.error = error
        if metadata:
            task_metrics.metadata.update(metadata)

        # Log to observability backend
        if self.observability:
            self._log_task_event(task_metrics)

    def complete_orchestration(self) -> OrchestrationMetrics:
        """
        Mark orchestration as complete.

        Returns:
            Final metrics for the orchestration
        """
        self.metrics.end_time = time.time()
        self.metrics.finalize()

        # Log orchestration completion
        if self.observability:
            self._log_orchestration_complete()

        return self.metrics

    def get_metrics(self) -> OrchestrationMetrics:
        """Get current metrics."""
        return self.metrics

    def _log_task_event(self, task_metrics: TaskMetrics) -> None:
        """Log task event to observability backend."""
        try:
            event = {
                "event_type": "task_execution",
                "execution_id": self.execution_id,
                "task_name": task_metrics.task_name,
                "tool_name": task_metrics.tool_name,
                "status": task_metrics.status,
                "duration_ms": task_metrics.duration_ms,
                "error": task_metrics.error,
                "attempt": task_metrics.attempt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.observability.log(event)
        except Exception as e:
            # Don't crash if logging fails
            print(f"Warning: Failed to log task event: {e}")

    def _log_orchestration_complete(self) -> None:
        """Log orchestration completion to observability backend."""
        try:
            event = {
                "event_type": "orchestration_complete",
                "execution_id": self.execution_id,
                "total_tasks": self.metrics.total_tasks,
                "succeeded_tasks": self.metrics.succeeded_tasks,
                "failed_tasks": self.metrics.failed_tasks,
                "skipped_tasks": self.metrics.skipped_tasks,
                "total_duration_ms": self.metrics.duration_ms,
                "success_rate": self.metrics.success_rate(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.observability.log(event)
        except Exception as e:
            # Don't crash if logging fails
            print(f"Warning: Failed to log orchestration event: {e}")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionTracker(execution_id={self.execution_id}, "
            f"tasks={len(self.metrics.task_metrics)})"
        )
