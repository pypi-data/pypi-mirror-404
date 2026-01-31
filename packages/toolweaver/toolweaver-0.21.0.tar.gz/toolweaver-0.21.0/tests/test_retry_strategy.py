"""Tests for retry strategy."""

from typing import Any

import pytest

from orchestrator.adapters.orchestrator_interface import (
    ToolCall,
    ToolSchema,
)
from orchestrator.adapters.production.retry_strategy import (
    RetryReason,
    RetryResult,
    RetryStrategy,
    create_aggressive_retry_strategy,
    create_conservative_retry_strategy,
    create_default_retry_strategy,
)


class TestRetryStrategyBasics:
    """Test basic retry strategy functionality."""

    def test_initialization(self) -> None:
        """Test retry strategy initialization."""
        strategy = RetryStrategy(
            max_retries=5,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=1.5,
        )

        assert strategy.max_retries == 5
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 30.0
        assert strategy.exponential_base == 1.5

    def test_exponential_backoff_calculation(self) -> None:
        """Test exponential backoff delay calculation."""
        strategy = RetryStrategy(base_delay=1.0, exponential_base=2.0, max_delay=60.0)

        # Test exponential growth
        assert strategy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert strategy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert strategy.calculate_delay(2) == 4.0  # 1 * 2^2
        assert strategy.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_max_delay_cap(self) -> None:
        """Test that delay is capped at max_delay."""
        strategy = RetryStrategy(base_delay=10.0, exponential_base=2.0, max_delay=30.0)

        # Should cap at 30.0
        assert strategy.calculate_delay(0) == 10.0
        assert strategy.calculate_delay(1) == 20.0
        assert strategy.calculate_delay(2) == 30.0  # Would be 40, capped at 30
        assert strategy.calculate_delay(3) == 30.0  # Would be 80, capped at 30

    def test_factory_functions(self) -> None:
        """Test factory functions create correct strategies."""
        default = create_default_retry_strategy()
        assert default.max_retries == 3
        assert default.base_delay == 1.0

        aggressive = create_aggressive_retry_strategy()
        assert aggressive.max_retries == 5
        assert aggressive.base_delay == 0.5

        conservative = create_conservative_retry_strategy()
        assert conservative.max_retries == 2
        assert conservative.base_delay == 2.0


class TestRetryableErrors:
    """Test error classification for retries."""

    def test_rate_limit_error_detection(self) -> None:
        """Test rate limit errors are detected as retriable."""
        strategy = RetryStrategy()

        error = Exception("Rate limit exceeded")
        is_retriable, reason = strategy.is_retriable_error(error)

        assert is_retriable is True
        assert reason == RetryReason.RATE_LIMIT

    def test_timeout_error_detection(self) -> None:
        """Test timeout errors are detected as retriable."""
        strategy = RetryStrategy()

        error = Exception("Request timed out")
        is_retriable, reason = strategy.is_retriable_error(error)

        assert is_retriable is True
        assert reason == RetryReason.TIMEOUT

    def test_non_retriable_error(self) -> None:
        """Test non-retriable errors are detected."""
        strategy = RetryStrategy()

        error = Exception("Invalid API key")
        is_retriable, reason = strategy.is_retriable_error(error)

        assert is_retriable is False


class TestExecuteWithRetry:
    """Test execute_with_retry functionality."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self) -> None:
        """Test successful execution without retries."""
        strategy = RetryStrategy(max_retries=3)

        async def success_func() -> str:
            return "success"

        result = await strategy.execute_with_retry(success_func)

        assert result.success is True
        assert result.final_result == "success"
        assert result.total_retries == 0
        assert len(result.attempts) == 0

    @pytest.mark.asyncio
    async def test_retry_on_retriable_error(self) -> None:
        """Test retry on retriable error."""
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)
        call_count = 0

        async def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded")
            return "success"

        result = await strategy.execute_with_retry(flaky_func)

        assert result.success is True
        assert result.final_result == "success"
        assert result.total_retries == 2
        assert len(result.attempts) == 2

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self) -> None:
        """Test behavior when max retries are exhausted."""
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)

        async def always_fail() -> str:
            raise Exception("Rate limit exceeded")

        result = await strategy.execute_with_retry(always_fail)

        assert result.success is False
        assert result.error_message == "Rate limit exceeded"
        assert result.total_retries == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retriable_error(self) -> None:
        """Test no retry on non-retriable error."""
        strategy = RetryStrategy(max_retries=3, base_delay=0.01)

        async def fail_auth() -> str:
            raise Exception("Invalid API key")

        result = await strategy.execute_with_retry(fail_auth)

        assert result.success is False
        assert result.total_retries == 0
        assert len(result.attempts) == 0


class TestToolCallRetry:
    """Test tool call retry with validation."""

    @pytest.mark.asyncio
    async def test_successful_tool_call_with_validation(self) -> None:
        """Test successful tool call with validation."""
        strategy = RetryStrategy(max_retries=3, validate_before_execution=True)

        schema = ToolSchema(
            name="test_tool",
            description="Test",
            parameters={"properties": {"x": {"type": "string"}}},
            required=["x"],
        )

        tool_call = ToolCall(tool_name="test_tool", parameters={"x": "value"})

        async def tool_func(x: str) -> str:
            return f"result: {x}"

        result = await strategy.execute_tool_call_with_retry(
            tool_call, schema, tool_func
        )

        assert result.success is True
        assert result.final_result == "result: value"

    @pytest.mark.asyncio
    async def test_validation_error_without_orchestrator(self) -> None:
        """Test validation error without orchestrator for correction."""
        strategy = RetryStrategy(max_retries=2, validate_before_execution=True)

        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={"properties": {"x": {"type": "string"}}},
            required=["x"],
        )

        # Invalid tool call (missing required param)
        tool_call = ToolCall(tool_name="test", parameters={})

        async def tool_func(**kwargs: Any) -> str:
            return "result"

        result = await strategy.execute_tool_call_with_retry(
            tool_call, schema, tool_func
        )

        assert result.success is False
        assert result.error_message is not None
        assert "Validation failed" in result.error_message

    @pytest.mark.asyncio
    async def test_retry_on_execution_error(self) -> None:
        """Test retry on execution error."""
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)

        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={"properties": {"x": {"type": "string"}}},
            required=["x"],
        )

        tool_call = ToolCall(tool_name="test", parameters={"x": "value"})
        call_count = 0

        async def flaky_tool(x: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded")
            return "success"

        result = await strategy.execute_tool_call_with_retry(
            tool_call, schema, flaky_tool
        )

        assert result.success is True
        assert result.total_retries == 2


class TestRetryStatistics:
    """Test retry statistics collection."""

    def test_get_retry_stats_no_retries(self) -> None:
        """Test statistics with no retries."""
        strategy = RetryStrategy()
        result = RetryResult(success=True, final_result="data")

        stats = strategy.get_retry_stats(result)

        assert stats["total_attempts"] == 1
        assert stats["total_retries"] == 0
        assert stats["total_delay"] == 0.0
        assert stats["success"] is True

    def test_get_retry_stats_with_retries(self) -> None:
        """Test statistics with retries."""
        strategy = RetryStrategy()
        result = RetryResult(success=True, final_result="data")

        result.add_attempt(RetryReason.RATE_LIMIT, "Rate limit", 1.0)
        result.add_attempt(RetryReason.RATE_LIMIT, "Rate limit", 2.0)

        stats = strategy.get_retry_stats(result)

        assert stats["total_attempts"] == 3
        assert stats["total_retries"] == 2
        assert stats["total_delay"] == 3.0
        assert stats["avg_delay"] == 1.5
        assert stats["reasons"]["rate_limit"] == 2

    def test_get_retry_stats_multiple_reasons(self) -> None:
        """Test statistics with multiple retry reasons."""
        strategy = RetryStrategy()
        result = RetryResult(success=False, final_result=None)

        result.add_attempt(RetryReason.RATE_LIMIT, "Rate limit", 1.0)
        result.add_attempt(RetryReason.TIMEOUT, "Timeout", 2.0)
        result.add_attempt(RetryReason.RATE_LIMIT, "Rate limit", 4.0)

        stats = strategy.get_retry_stats(result)

        assert stats["total_retries"] == 3
        assert stats["reasons"]["rate_limit"] == 2
        assert stats["reasons"]["timeout"] == 1


class TestRetryResult:
    """Test RetryResult class."""

    def test_add_attempt(self) -> None:
        """Test adding retry attempts."""
        result = RetryResult(success=False, final_result=None)

        result.add_attempt(RetryReason.TIMEOUT, "Timeout error", 1.5)

        assert len(result.attempts) == 1
        assert result.total_retries == 1
        assert result.total_delay == 1.5
        assert result.attempts[0].attempt_number == 1
        assert result.attempts[0].reason == RetryReason.TIMEOUT

    def test_multiple_attempts(self) -> None:
        """Test multiple retry attempts."""
        result = RetryResult(success=False, final_result=None)

        result.add_attempt(RetryReason.RATE_LIMIT, "Error 1", 1.0)
        result.add_attempt(RetryReason.TIMEOUT, "Error 2", 2.0)
        result.add_attempt(RetryReason.RATE_LIMIT, "Error 3", 4.0)

        assert len(result.attempts) == 3
        assert result.total_retries == 3
        assert result.total_delay == 7.0
        assert result.attempts[0].attempt_number == 1
        assert result.attempts[1].attempt_number == 2
        assert result.attempts[2].attempt_number == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
