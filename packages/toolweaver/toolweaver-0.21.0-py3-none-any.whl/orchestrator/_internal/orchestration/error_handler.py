"""
Error handling and recovery for orchestration.

Provides strategies for handling task failures during orchestration.
"""

import time
from enum import Enum


class ErrorRecoveryStrategy(str, Enum):
    """Strategies for recovering from task errors."""

    FAIL_FAST = "fail_fast"  # Stop orchestration on error
    RETRY = "retry"  # Retry task up to retry_count
    SKIP = "skip"  # Skip failed task and continue
    ROLLBACK = "rollback"  # Undo previous tasks and stop


class OrchestrationError(Exception):
    """Base exception for orchestration errors."""

    pass


class TaskExecutionError(OrchestrationError):
    """Error during task execution."""

    def __init__(self, task_name: str, tool_name: str, error: Exception, attempt: int = 1):
        self.task_name = task_name
        self.tool_name = tool_name
        self.error = error
        self.attempt = attempt
        super().__init__(
            f"Task '{task_name}' (tool: {tool_name}) failed on attempt {attempt}: {error}"
        )


class OrchestrationFailedError(OrchestrationError):
    """Orchestration failed after all recovery attempts."""

    def __init__(self, message: str, errors: list[Exception] | None = None):
        self.errors = errors or []
        super().__init__(message)


class DependencyNotMetError(OrchestrationError):
    """Task depends on another task that hasn't completed."""

    def __init__(self, task_name: str, depends_on: str):
        self.task_name = task_name
        self.depends_on = depends_on
        super().__init__(
            f"Task '{task_name}' depends on '{depends_on}' but it hasn't completed or failed"
        )


class ParameterResolutionError(OrchestrationError):
    """Error resolving task parameters."""

    def __init__(self, task_name: str, error: Exception):
        self.task_name = task_name
        super().__init__(f"Failed to resolve parameters for task '{task_name}': {error}")


class ErrorHandler:
    """
    Handle and recover from task execution errors.

    Supports multiple recovery strategies with configurable retry logic.
    """

    def __init__(self, default_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.FAIL_FAST):
        """
        Initialize ErrorHandler.

        Args:
            default_strategy: Default recovery strategy
        """
        self.default_strategy = default_strategy
        self.errors: list[Exception] = []

    def handle_error(
        self,
        task_name: str,
        tool_name: str,
        error: Exception,
        retry_count: int,
        strategy: ErrorRecoveryStrategy | None = None,
    ) -> str | None:
        """
        Handle a task error based on recovery strategy.

        Args:
            task_name: Name of the failed task
            tool_name: Name of the tool being executed
            error: The exception that occurred
            retry_count: Number of remaining retries
            strategy: Recovery strategy (uses default if None)

        Returns:
            "retry" if task should be retried
            "skip" if task should be skipped
            "stop" if orchestration should stop
            None if error is unrecoverable

        Raises:
            TaskExecutionError: Always raised (caller decides action)
        """
        strategy = strategy or self.default_strategy
        task_error = TaskExecutionError(task_name, tool_name, error)
        self.errors.append(task_error)

        if strategy == ErrorRecoveryStrategy.FAIL_FAST:
            # Stop immediately
            return "stop"

        elif strategy == ErrorRecoveryStrategy.RETRY:
            # Retry if attempts remain
            if retry_count > 0:
                return "retry"
            else:
                return "stop"

        elif strategy == ErrorRecoveryStrategy.SKIP:
            # Skip this task and continue
            return "skip"

        elif strategy == ErrorRecoveryStrategy.ROLLBACK:
            # Rollback and stop (implementation in orchestrator)
            return "stop"

        # Exhaustive check - strategy should be handled above
        raise AssertionError(f"Unhandled strategy: {strategy}")

    def should_continue(self, error: Exception, strategy: ErrorRecoveryStrategy) -> bool:
        """
        Determine if orchestration should continue after error.

        Args:
            error: The exception that occurred
            strategy: Recovery strategy

        Returns:
            True if orchestration should continue, False otherwise
        """
        if strategy == ErrorRecoveryStrategy.FAIL_FAST:
            return False

        if strategy == ErrorRecoveryStrategy.SKIP:
            return True

        if strategy == ErrorRecoveryStrategy.RETRY:
            # Only continue if retries remain (decided by caller)
            return True

        if strategy == ErrorRecoveryStrategy.ROLLBACK:
            return False

        # Exhaustive check - strategy should be handled above
        raise AssertionError(f"Unhandled strategy: {strategy}")

    def add_error(self, error: Exception) -> None:
        """Add error to error list."""
        self.errors.append(error)

    def get_errors(self) -> list[Exception]:
        """Get all errors that occurred."""
        return list(self.errors)

    def clear_errors(self) -> None:
        """Clear error list."""
        self.errors.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"ErrorHandler(strategy={self.default_strategy.value}, errors={len(self.errors)})"


class RetryPolicy:
    """Policy for retrying failed tasks."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        max_backoff: float = 60.0,
    ):
        """
        Initialize RetryPolicy.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff (1.0 = no backoff)
            max_backoff: Maximum backoff time in seconds
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff

    def should_retry(self, attempt: int) -> bool:
        """Check if we should retry based on attempt number."""
        return attempt <= self.max_retries

    def get_backoff_time(self, attempt: int) -> float:
        """
        Get backoff time before retry.

        Args:
            attempt: The attempt number (1-indexed)

        Returns:
            Time to wait in seconds
        """
        if self.backoff_factor <= 1.0:
            return 0.0  # No backoff

        # Exponential backoff: backoff_factor ^ attempt
        backoff = (self.backoff_factor**attempt) - 1
        return min(backoff, self.max_backoff)

    def wait_before_retry(self, attempt: int) -> None:
        """Wait before retry (blocking)."""
        backoff = self.get_backoff_time(attempt)
        if backoff > 0:
            time.sleep(backoff)
