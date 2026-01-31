"""
Task model for orchestration.

Defines the Task class that represents a single step in an orchestration.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Status of a task execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class Task:
    """
    Represents a single tool execution step in an orchestration.

    Attributes:
        name: Unique identifier for this task
        tool_name: Name of the tool to execute
        params: Input parameters to pass to the tool
        depends_on: List of task names that must complete before this task
        retry_count: Number of times to retry on failure
        timeout: Maximum seconds to wait for task completion
        transform: Optional function to transform the output
        metadata: Additional metadata about the task
    """

    name: str
    tool_name: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    retry_count: int = 3
    timeout: float = 30.0
    transform: Callable[[Any], Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate task configuration."""
        if not self.name:
            raise ValueError("Task name cannot be empty")
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    def has_param_reference(self) -> bool:
        """Check if task has parameters that reference other tasks."""
        for value in self.params.values():
            if isinstance(value, str) and value.startswith("@"):
                return True
        return False

    def get_dependencies_from_params(self) -> list[str]:
        """Extract task dependencies from parameter references."""
        deps = set()
        for value in self.params.values():
            if isinstance(value, str) and value.startswith("@"):
                # Format: "@task_name" or "@task_name.output"
                task_ref = value[1:].split(".")[0]
                deps.add(task_ref)
        return list(deps)
