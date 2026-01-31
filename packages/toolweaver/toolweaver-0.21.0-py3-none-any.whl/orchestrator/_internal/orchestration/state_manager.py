"""
State management for orchestration.

Manages execution state across tool executions with both in-memory
and persistent storage via Phase -1 StorageBackend.
"""

import uuid
from typing import Any

from .task import Task


class StateManager:
    """
    Manage orchestration state between tool executions.

    Handles:
    - In-memory state for current execution
    - Persistent state via StorageBackend (Phase -1)
    - Parameter resolution with task references
    - State cleanup on completion
    """

    def __init__(self, storage_backend: Any = None, execution_id: str | None = None) -> None:
        """
        Initialize StateManager.

        Args:
            storage_backend: Phase -1 StorageBackend instance (optional)
            execution_id: Unique ID for this orchestration (auto-generated if None)
        """
        self.storage = storage_backend
        self.execution_id = execution_id or str(uuid.uuid4())
        self._memory_state: dict[str, Any] = {}

    def save_state(self, task_name: str, result: Any, persist: bool = True) -> None:
        """
        Save task result to memory and optionally to persistent storage.

        Args:
            task_name: Name of the task that produced the result
            result: The result to save
            persist: Whether to save to StorageBackend (if available)
        """
        # Always save to memory (fast access)
        self._memory_state[task_name] = result

        # Optionally persist to storage backend
        if persist and self.storage:
            key = self._storage_key(task_name)
            self.storage.save(key, result)

    def load_state(self, task_name: str) -> Any:
        """
        Load task result from memory or persistent storage.

        Args:
            task_name: Name of the task

        Returns:
            The saved result or None if not found

        Raises:
            KeyError: If task result not found
        """
        # Check memory first (fast path)
        if task_name in self._memory_state:
            return self._memory_state[task_name]

        # Check persistent storage
        if self.storage:
            key = self._storage_key(task_name)
            try:
                result = self.storage.load(key)
                # Cache in memory for future access
                self._memory_state[task_name] = result
                return result
            except Exception:
                pass

        raise KeyError(f"Task result not found: {task_name}")

    def has_state(self, task_name: str) -> bool:
        """Check if state exists for a task."""
        if task_name in self._memory_state:
            return True

        if self.storage:
            key = self._storage_key(task_name)
            try:
                self.storage.load(key)
                return True
            except Exception:
                pass

        return False

    def resolve_params(self, task: Task, state: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve task parameters, substituting task references.

        References are in format "@task_name" or "@task_name.output".

        Args:
            task: Task with parameters to resolve
            state: Current execution state

        Returns:
            Resolved parameters with references replaced by actual values

        Raises:
            ValueError: If referenced task not found in state
        """
        resolved = {}

        for key, value in task.params.items():
            if isinstance(value, str) and value.startswith("@"):
                # Reference to another task's output
                # Format: "@task_name" or "@task_name.output"
                parts = value[1:].split(".")
                task_ref = parts[0]

                if task_ref not in state:
                    raise ValueError(
                        f"Task '{task.name}' references '{task_ref}' "
                        f"but it is not in execution state"
                    )

                resolved[key] = state[task_ref]
            else:
                resolved[key] = value

        return resolved

    def get_execution_state(self) -> dict[str, Any]:
        """Get current execution state (all task results)."""
        return dict(self._memory_state)

    def clear_state(self) -> None:
        """Clear in-memory state (storage persists)."""
        self._memory_state.clear()

    def cleanup(self) -> None:
        """Cleanup state from persistent storage (optional)."""
        # Only cleanup if explicitly called
        # Useful for tests but generally don't auto-cleanup
        pass

    def _storage_key(self, task_name: str) -> str:
        """Generate storage key for a task."""
        return f"execution_{self.execution_id}_task_{task_name}"

    def __repr__(self) -> str:
        """String representation."""
        return f"StateManager(execution_id={self.execution_id}, tasks={len(self._memory_state)})"
