"""Retry strategy for tool call execution with intelligent error recovery.

This module provides retry logic with exponential backoff and orchestrator
feedback for auto-correcting invalid tool calls.
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    ToolCall,
    ToolSchema,
)
from orchestrator.adapters.production.validator import ToolCallValidator


class RetryReason(Enum):
    """Reasons for retry attempts."""

    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"


@dataclass
class RetryAttempt:
    """Record of a single retry attempt."""

    attempt_number: int
    reason: RetryReason
    error_message: str
    delay_seconds: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class RetryResult:
    """Result of retry execution."""

    success: bool
    final_result: Any
    attempts: list[RetryAttempt] = field(default_factory=list)
    total_retries: int = 0
    total_delay: float = 0.0
    error_message: str | None = None

    def add_attempt(
        self,
        reason: RetryReason,
        error: str,
        delay: float,
    ) -> None:
        """Add a retry attempt to the result."""
        self.attempts.append(
            RetryAttempt(
                attempt_number=len(self.attempts) + 1,
                reason=reason,
                error_message=error,
                delay_seconds=delay,
            )
        )
        self.total_retries += 1
        self.total_delay += delay


class RetryStrategy:
    """Retry strategy with exponential backoff and validation."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        validate_before_execution: bool = True,
    ):
        """
        Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            validate_before_execution: Whether to validate tool calls before execution
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.validate_before_execution = validate_before_execution

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)

    def is_retriable_error(self, error: Exception) -> tuple[bool, RetryReason]:
        """
        Determine if an error is retriable.

        Args:
            error: Exception that occurred

        Returns:
            Tuple of (is_retriable, reason)
        """
        error_str = str(error).lower()

        # Rate limiting errors
        if "rate limit" in error_str or "429" in error_str:
            return True, RetryReason.RATE_LIMIT

        # Timeout errors
        if "timeout" in error_str or "timed out" in error_str:
            return True, RetryReason.TIMEOUT

        # Execution errors (generic)
        if "execution" in error_str:
            return True, RetryReason.EXECUTION_ERROR

        # Default: not retriable
        return False, RetryReason.EXECUTION_ERROR

    async def execute_with_retry(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            RetryResult with execution outcome and retry details
        """
        result = RetryResult(success=False, final_result=None)
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute function
                output = await func(*args, **kwargs)
                result.success = True
                result.final_result = output
                return result

            except Exception as e:
                last_error = e

                # Check if we should retry
                if attempt >= self.max_retries:
                    break

                is_retriable, reason = self.is_retriable_error(e)
                if not is_retriable:
                    break

                # Calculate delay and wait
                delay = self.calculate_delay(attempt)
                result.add_attempt(reason, str(e), delay)

                await asyncio.sleep(delay)

        # All retries exhausted
        result.success = False
        result.error_message = str(last_error) if last_error else "Unknown error"
        return result

    async def execute_tool_call_with_retry(
        self,
        tool_call: ToolCall,
        tool_schema: ToolSchema,
        tool_func: Callable[..., Coroutine[Any, Any, Any]],
        orchestrator: OrchestratorBackend | None = None,
    ) -> RetryResult:
        """
        Execute a tool call with validation and retry logic.

        Args:
            tool_call: Tool call to execute
            tool_schema: Schema for validation
            tool_func: Async function that executes the tool
            orchestrator: Optional orchestrator for feedback-based correction

        Returns:
            RetryResult with execution outcome
        """
        result = RetryResult(success=False, final_result=None)

        for attempt in range(self.max_retries + 1):
            # Validate before execution if enabled
            if self.validate_before_execution:
                is_valid, errors = ToolCallValidator.validate(tool_call, tool_schema)

                if not is_valid:
                    if attempt >= self.max_retries:
                        error_summary = ToolCallValidator.get_error_summary(errors)
                        result.error_message = f"Validation failed: {error_summary}"
                        break

                    # Attempt correction via orchestrator
                    if orchestrator:
                        delay = self.calculate_delay(attempt)
                        result.add_attempt(
                            RetryReason.VALIDATION_ERROR,
                            f"Validation errors: {len(errors)}",
                            delay,
                        )

                        # Ask orchestrator to fix the tool call
                        error_feedback = ToolCallValidator.get_error_summary(errors)
                        try:
                            corrected_plan = await orchestrator.plan(  # type: ignore[misc]
                                f"Fix tool call parameters. Errors: {error_feedback}"
                            )

                            if corrected_plan.tool_calls:
                                tool_call = corrected_plan.tool_calls[0]
                                await asyncio.sleep(delay)
                                continue
                        except Exception:
                            pass  # Correction failed, continue to retry

                    else:
                        # No orchestrator, can't correct
                        error_summary = ToolCallValidator.get_error_summary(errors)
                        result.error_message = f"Validation failed: {error_summary}"
                        break

            # Execute tool
            try:
                output = await tool_func(**tool_call.parameters)
                result.success = True
                result.final_result = output
                return result

            except Exception as e:
                if attempt >= self.max_retries:
                    result.error_message = str(e)
                    break

                is_retriable, reason = self.is_retriable_error(e)
                if not is_retriable:
                    result.error_message = f"Non-retriable error: {e}"
                    break

                delay = self.calculate_delay(attempt)
                result.add_attempt(reason, str(e), delay)
                await asyncio.sleep(delay)

        return result

    def get_retry_stats(self, result: RetryResult) -> dict[str, Any]:
        """
        Get statistics from retry result.

        Args:
            result: RetryResult to analyze

        Returns:
            Dictionary with retry statistics
        """
        if not result.attempts:
            return {
                "total_attempts": 1,
                "total_retries": 0,
                "total_delay": 0.0,
                "reasons": {},
                "success": result.success,
            }

        reasons: dict[str, int] = {}
        for attempt in result.attempts:
            reason_name = attempt.reason.value
            reasons[reason_name] = reasons.get(reason_name, 0) + 1

        return {
            "total_attempts": len(result.attempts) + 1,
            "total_retries": result.total_retries,
            "total_delay": result.total_delay,
            "reasons": reasons,
            "success": result.success,
            "avg_delay": (
                result.total_delay / len(result.attempts) if result.attempts else 0.0
            ),
        }


# Convenience factory functions
def create_default_retry_strategy() -> RetryStrategy:
    """Create retry strategy with default settings."""
    return RetryStrategy(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        validate_before_execution=True,
    )


def create_aggressive_retry_strategy() -> RetryStrategy:
    """Create retry strategy with aggressive settings for critical operations."""
    return RetryStrategy(
        max_retries=5,
        base_delay=0.5,
        max_delay=30.0,
        exponential_base=1.5,
        validate_before_execution=True,
    )


def create_conservative_retry_strategy() -> RetryStrategy:
    """Create retry strategy with conservative settings to minimize API calls."""
    return RetryStrategy(
        max_retries=2,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=3.0,
        validate_before_execution=True,
    )
