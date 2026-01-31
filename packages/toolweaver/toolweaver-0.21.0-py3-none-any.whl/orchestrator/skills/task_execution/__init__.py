"""
Task Execution Skill

Wrapper around orchestrator._internal.execution module for executing
and monitoring tasks.
"""

from typing import Any, Optional

try:
    from orchestrator._internal.execution import Executor  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    Executor = None

# Global executor instance
_executor = None


def get_executor() -> Executor:
    """Get or create the global executor instance."""
    global _executor
    if _executor is None:
        _executor = Executor()
    return _executor


def execute_task(
    task_id: str, task: str, agent_id: str | None = None, timeout: int = 300
) -> dict[str, Any]:
    """Execute a single task."""
    executor = get_executor()

    if hasattr(executor, "execute"):
        result = executor.execute(task_id=task_id, task=task, agent_id=agent_id, timeout=timeout)
    else:
        result = {"task_id": task_id, "status": "pending"}

    return {
        "task_id": task_id,
        "task": task,
        "status": getattr(result, "status", "unknown"),
        "result": str(result) if result else None,
    }


def get_task_status(task_id: str) -> dict[str, Any]:
    """Get current status of a task."""
    executor = get_executor()

    if hasattr(executor, "get_status"):
        status = executor.get_status(task_id)
    else:
        status = "unknown"

    return {"task_id": task_id, "status": status, "running": status == "running"}


def cancel_task(task_id: str, force: bool = False) -> dict[str, Any]:
    """Cancel a running task."""
    executor = get_executor()

    if hasattr(executor, "cancel"):
        cancelled = executor.cancel(task_id, force=force)
    else:
        cancelled = False

    return {"task_id": task_id, "cancelled": cancelled, "force": force}


def retry_task(task_id: str, max_retries: int = 3) -> dict[str, Any]:
    """Retry a failed task."""
    executor = get_executor()

    if hasattr(executor, "retry"):
        result = executor.retry(task_id, max_retries=max_retries)
    else:
        result = None

    return {
        "task_id": task_id,
        "retried": True,
        "max_retries": max_retries,
        "result": str(result) if result else None,
    }


def get_execution_stats() -> dict[str, Any]:
    """Get execution statistics."""
    executor = get_executor()

    stats = {
        "total_tasks": getattr(executor, "total_tasks", 0),
        "completed_tasks": getattr(executor, "completed_tasks", 0),
        "failed_tasks": getattr(executor, "failed_tasks", 0),
        "avg_execution_time": getattr(executor, "avg_time", 0),
    }

    return stats


__all__ = ["execute_task", "get_task_status", "cancel_task", "retry_task", "get_execution_stats"]
