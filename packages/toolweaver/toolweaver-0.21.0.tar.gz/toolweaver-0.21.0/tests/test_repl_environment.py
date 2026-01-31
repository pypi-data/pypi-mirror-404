"""
Tests for REPL Environment (Recursive Language Models).

Tests basic code execution, timeout handling, output capture,
recursive call support, and strategy execution (peek/grep/partition).
"""

from typing import Any

import pytest

from orchestrator.tools.repl_environment import (
    GrepStrategy,
    PartitionStrategy,
    PeekStrategy,
    REPLEnvironment,
)


@pytest.fixture
def simple_context() -> Any:
    """Simple text context."""
    return "Hello world! This is a test context with some numbers: 123, 456, 789."


@pytest.fixture
def structured_context() -> Any:
    """Structured JSON-like context."""
    return """
    [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"}
    ]
    """


@pytest.fixture
def large_context() -> Any:
    """Large context for partitioning tests."""
    return "Line " + "\nLine ".join(str(i) for i in range(10000))  # ~50KB


@pytest.fixture
def repl_with_simple_context(simple_context: Any) -> Any:
    """REPL environment with simple context."""
    return REPLEnvironment(context=simple_context, debug=True)


@pytest.fixture
def repl_with_structured_context(structured_context: Any) -> Any:
    """REPL environment with structured context."""
    return REPLEnvironment(context=structured_context, debug=True)


@pytest.fixture
def repl_with_large_context(large_context: Any) -> Any:
    """REPL environment with large context."""
    return REPLEnvironment(context=large_context, debug=True)


class TestREPLBasicExecution:
    """Test basic code execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_code(self, repl_with_simple_context: Any) -> None:
        """Test executing simple Python code."""
        code = "x = 1 + 1"
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert result.error is None
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execute_print_statement(self, repl_with_simple_context: Any) -> None:
        """Test code that prints output."""
        code = "print('Hello from REPL')"
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Hello from REPL" in result.output
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_multiple_prints(self, repl_with_simple_context: Any) -> None:
        """Test multiple print statements."""
        code = """
print('First line')
print('Second line')
print('Third line')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "First line" in result.output
        assert "Second line" in result.output
        assert "Third line" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_variables(self, repl_with_simple_context: Any) -> None:
        """Test code that sets variables."""
        code = """
result = 42
name = 'test'
"""
        result_obj = await repl_with_simple_context.execute(code)

        assert result_obj.success is True
        assert repl_with_simple_context.get_variable("result") == 42
        assert repl_with_simple_context.get_variable("name") == "test"

    @pytest.mark.asyncio
    async def test_execute_arithmetic(self, repl_with_simple_context: Any) -> None:
        """Test arithmetic operations."""
        code = """
result = 10 * 5 + 3
print(f'Result: {result}')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Result: 53" in result.output

    @pytest.mark.asyncio
    async def test_execute_string_operations(self, repl_with_simple_context: Any) -> None:
        """Test string operations."""
        code = """
text = 'Hello'
result = text.upper()
print(result)
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "HELLO" in result.output

    @pytest.mark.asyncio
    async def test_execute_list_operations(self, repl_with_simple_context: Any) -> None:
        """Test list operations."""
        code = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f'Sum: {total}')
print(f'Length: {len(numbers)}')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Sum: 15" in result.output
        assert "Length: 5" in result.output


class TestContextAccess:
    """Test accessing context_var."""

    @pytest.mark.asyncio
    async def test_access_context_var(self, repl_with_simple_context: Any) -> None:
        """Test accessing context_var."""
        code = """
length = len(context_var)
print(f'Context length: {length}')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Context length:" in result.output

    @pytest.mark.asyncio
    async def test_context_var_string_slicing(self, repl_with_simple_context: Any, simple_context: Any) -> None:
        """Test slicing context_var."""
        code = """
first_10 = context_var[:10]
print(first_10)
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert simple_context[:10] in result.output

    @pytest.mark.asyncio
    async def test_context_var_search(self, repl_with_simple_context: Any) -> None:
        """Test searching in context_var."""
        code = """
if 'test' in context_var:
    print('Found test')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Found test" in result.output


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_syntax_error(self, repl_with_simple_context: Any) -> None:
        """Test syntax error handling."""
        code = "this is not valid python !!!"
        result = await repl_with_simple_context.execute(code)

        assert result.success is False
        assert result.error is not None
        assert "SyntaxError" in result.error or "Execution error" in result.error

    @pytest.mark.asyncio
    async def test_runtime_error(self, repl_with_simple_context: Any) -> None:
        """Test runtime error handling."""
        code = """
x = 1
y = 1 / 0  # Division by zero
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is False
        assert result.error is not None
        assert "ZeroDivisionError" in result.error

    @pytest.mark.asyncio
    async def test_undefined_variable_error(self, repl_with_simple_context: Any) -> None:
        """Test undefined variable error."""
        code = "print(undefined_variable)"
        result = await repl_with_simple_context.execute(code)

        assert result.success is False
        assert "NameError" in result.error

    @pytest.mark.asyncio
    async def test_type_error(self, repl_with_simple_context: Any) -> None:
        """Test type error handling."""
        code = """
x = 'string'
y = x + 5  # Can't add str and int
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is False
        assert "TypeError" in result.error

    @pytest.mark.asyncio
    async def test_error_preserves_previous_output(self, repl_with_simple_context: Any) -> None:
        """Test that errors preserve output before error."""
        code = """
print('Before error')
x = 1 / 0
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is False
        assert "Before error" in result.output


class TestTimeoutHandling:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_on_infinite_loop(self) -> None:
        """Test timeout on infinite loop."""
        repl = REPLEnvironment(context="test", max_timeout_seconds=1, debug=True)
        # Inject time module for testing
        import time
        repl.globals["time"] = time

        code = """
start = time.time()
# Run for 2 seconds (longer than timeout but finite to avoid zombie threads)
while time.time() - start < 2:
    pass
"""
        result = await repl.execute(code)

        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_timeout_on_sleep(self) -> None:
        """Test timeout on sleep."""
        repl = REPLEnvironment(context="test", max_timeout_seconds=1, debug=True)
        import time
        repl.globals["time"] = time

        code = """
# Sleep for 2 seconds (longer than timeout but finite)
time.sleep(2)
"""
        result = await repl.execute(code)

        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_no_timeout_on_fast_code(self, repl_with_simple_context: Any) -> None:
        """Test fast code completes within timeout."""
        code = """
result = sum(range(1000))
print(result)
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert result.execution_time_ms < 1000  # Should be very fast


class TestPeekStrategy:
    """Test peek strategy."""

    @pytest.mark.asyncio
    async def test_peek_first_chars(self, repl_with_simple_context: Any, simple_context: Any) -> None:
        """Test peek shows first characters."""
        output = await PeekStrategy.peek(repl_with_simple_context, peek_chars=20)

        assert simple_context[:20] in output

    @pytest.mark.asyncio
    async def test_peek_respects_limit(self, repl_with_large_context: Any) -> None:
        """Test peek respects character limit."""
        output = await PeekStrategy.peek(repl_with_large_context, peek_chars=100)

        # Should have output, but not the full large context
        assert len(output) > 0
        assert len(output) < 5000  # Much less than full context


class TestGrepStrategy:
    """Test grep strategy."""

    @pytest.mark.asyncio
    async def test_grep_finds_matches(self, repl_with_simple_context: Any) -> None:
        """Test grep finds pattern matches."""
        output = await GrepStrategy.grep(repl_with_simple_context, pattern=r"\d+")

        # Should find numbers in context
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_grep_no_matches(self, repl_with_simple_context: Any) -> None:
        """Test grep with pattern that doesn't match."""
        output = await GrepStrategy.grep(repl_with_simple_context, pattern=r"ZZZZZZZ")

        # May show "Match 1:" with empty results or simple output
        assert isinstance(output, str)

    @pytest.mark.asyncio
    async def test_grep_email_pattern(self, repl_with_structured_context: Any) -> None:
        """Test grep with email pattern."""
        output = await GrepStrategy.grep(
            repl_with_structured_context, pattern=r"[\w\.-]+@[\w\.-]+\.\w+"
        )

        # Should find email addresses
        assert len(output) > 0


class TestPartitionStrategy:
    """Test partition strategy."""

    @pytest.mark.asyncio
    async def test_partition_creates_chunks(self, repl_with_large_context: Any) -> None:
        """Test partition creates chunks."""
        chunks = await PartitionStrategy.partition(repl_with_large_context, chunk_size=10000)

        assert len(chunks) > 1  # Should have multiple chunks
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_partition_chunk_size_respected(self, repl_with_large_context: Any) -> None:
        """Test chunk sizes are respected."""
        chunk_size = 5000
        chunks = await PartitionStrategy.partition(repl_with_large_context, chunk_size=chunk_size)

        # All chunks except possibly the last should be close to chunk_size
        for chunk in chunks[:-1]:
            assert len(chunk) <= chunk_size + 1  # Small buffer for edge cases

    @pytest.mark.asyncio
    async def test_partition_covers_all_context(self, repl_with_large_context: Any) -> None:
        """Test partition covers entire context."""
        chunks = await PartitionStrategy.partition(repl_with_large_context, chunk_size=20000)

        reassembled = "".join(chunks)
        assert reassembled == repl_with_large_context.context


class TestExecutionResult:
    """Test REPLExecutionResult structure."""

    @pytest.mark.asyncio
    async def test_result_has_all_fields(self, repl_with_simple_context: Any) -> None:
        """Test result has all expected fields."""
        code = "x = 1"
        result = await repl_with_simple_context.execute(code)

        assert hasattr(result, "success")
        assert hasattr(result, "output")
        assert hasattr(result, "error")
        assert hasattr(result, "execution_time_ms")
        assert hasattr(result, "recursive_calls")

    @pytest.mark.asyncio
    async def test_result_types(self, repl_with_simple_context: Any) -> None:
        """Test result field types."""
        code = "print('test')"
        result = await repl_with_simple_context.execute(code)

        assert isinstance(result.success, bool)
        assert isinstance(result.output, str)
        assert result.error is None or isinstance(result.error, str)
        assert isinstance(result.execution_time_ms, float)
        assert isinstance(result.recursive_calls, int)

    @pytest.mark.asyncio
    async def test_result_timing_positive(self, repl_with_simple_context: Any) -> None:
        """Test execution time is positive."""
        code = "x = sum(range(100000))"
        result = await repl_with_simple_context.execute(code)

        assert result.execution_time_ms > 0


class TestVariableManagement:
    """Test get/set variable operations."""

    @pytest.mark.asyncio
    async def test_set_and_get_variable(self, repl_with_simple_context: Any) -> None:
        """Test setting and getting variables."""
        repl_with_simple_context.set_variable("my_var", 42)
        value = repl_with_simple_context.get_variable("my_var")

        assert value == 42

    @pytest.mark.asyncio
    async def test_get_nonexistent_variable(self, repl_with_simple_context: Any) -> None:
        """Test getting nonexistent variable returns None."""
        value = repl_with_simple_context.get_variable("nonexistent")

        assert value is None

    @pytest.mark.asyncio
    async def test_variables_persist_across_executions(self, repl_with_simple_context: Any) -> None:
        """Test variables set in code persist."""
        code1 = "x = 100"
        code2 = "y = x + 50; print(y)"

        await repl_with_simple_context.execute(code1)
        result = await repl_with_simple_context.execute(code2)

        assert result.success is True
        assert "150" in result.output


class TestDictContext:
    """Test REPL with dict context."""

    @pytest.mark.asyncio
    async def test_dict_context_string_representation(self) -> None:
        """Test REPL with dictionary context (stored as string)."""
        context = {"key1": "value1", "nested": {"key2": "value2"}}
        repl = REPLEnvironment(context=context, debug=True)

        code = "length = len(context_var); print(f'Context length: {length}')"
        result = await repl.execute(code)

        assert result.success is True
        assert "Context length:" in result.output

    @pytest.mark.asyncio
    async def test_access_dict_in_code(self) -> None:
        """Test accessing dict values in code."""
        context = {"data": [1, 2, 3, 4, 5]}
        repl = REPLEnvironment(context=context, debug=True)

        # String representation of dict is stored in context_var
        code = """
context_str = str(context_var)
print(f'Context length: {len(context_str)}')
"""
        result = await repl.execute(code)

        assert result.success is True


class TestComplexScenarios:
    """Test complex execution scenarios."""

    @pytest.mark.asyncio
    async def test_string_search_in_context(self, repl_with_structured_context: Any) -> None:
        """Test string search in context."""
        code = """
pattern = '"id"'
count = context_var.count(pattern)
print(f'Found {count} occurrences of id field')
"""
        result = await repl_with_structured_context.execute(code)

        assert result.success is True
        assert "Found" in result.output

    @pytest.mark.asyncio
    async def test_line_iteration(self, repl_with_large_context: Any) -> None:
        """Test iterating over lines in context."""
        code = """
lines = context_var.split('\\n')
print(f'Total lines: {len(lines)}')
print(f'First line: {lines[0][:50]}')
"""
        result = await repl_with_large_context.execute(code)

        assert result.success is True
        assert "Total lines:" in result.output

    @pytest.mark.asyncio
    async def test_character_count_analysis(self, repl_with_simple_context: Any) -> None:
        """Test character counting without Counter."""
        code = """
alpha_chars = [c for c in context_var if c.isalpha()]
print(f'Total alpha characters: {len(alpha_chars)}')
space_count = context_var.count(' ')
print(f'Spaces: {space_count}')
"""
        result = await repl_with_simple_context.execute(code)

        assert result.success is True
        assert "Total alpha characters:" in result.output
        assert "Spaces:" in result.output


class TestTokenEstimation:
    """Test token estimation."""

    def test_estimate_tokens_basic(self) -> None:
        """Test basic token estimation."""
        text = "x" * 1000
        tokens = REPLEnvironment.estimate_tokens(text, tokens_per_char=0.25)

        assert tokens == 250  # 1000 * 0.25

    def test_estimate_tokens_empty(self) -> None:
        """Test token estimation with empty text."""
        tokens = REPLEnvironment.estimate_tokens("")

        assert tokens == 0

    def test_estimate_tokens_custom_ratio(self) -> None:
        """Test token estimation with custom ratio."""
        text = "x" * 1000
        tokens = REPLEnvironment.estimate_tokens(text, tokens_per_char=0.5)

        assert tokens == 500


class TestDebugMode:
    """Test debug mode."""

    @pytest.mark.asyncio
    async def test_debug_mode_enabled(self, caplog: Any) -> None:
        """Test debug mode logs messages."""
        repl = REPLEnvironment(context="test", debug=True)

        code = "print('test')"
        result = await repl.execute(code)

        assert result.success is True
        # Debug logs should be written (if logging is captured)

    @pytest.mark.asyncio
    async def test_debug_mode_disabled(self) -> None:
        """Test debug mode can be disabled."""
        repl = REPLEnvironment(context="test", debug=False)

        code = "print('test')"
        result = await repl.execute(code)

        assert result.success is True
