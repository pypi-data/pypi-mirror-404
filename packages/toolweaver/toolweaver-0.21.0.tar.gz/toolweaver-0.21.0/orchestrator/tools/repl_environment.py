"""
REPL Environment for Recursive Language Models.

Provides a sandboxed Python execution environment where LMs can:
- Interact with context as a variable
- Execute arbitrary Python code
- Make recursive LM calls back to the orchestrator
- Partition/grep/analyze large contexts programmatically

Based on: Recursive Language Models (Zhang et al., Dec 2025)
https://arxiv.org/abs/2512.24601
"""

import asyncio
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class REPLExecutionResult:
    """Result from REPL code execution."""

    success: bool
    output: str
    error: str | None = None
    execution_time_ms: float = 0.0
    recursive_calls: int = 0  # Count of recursive LM calls made


class REPLEnvironment:
    """
    Sandboxed Python REPL for RLM context interaction.

    LMs can:
    1. Access context_var (the long context as a string or structured data)
    2. Execute Python code (grep, partition, regex, etc.)
    3. Call recursive_llm_call(text, model) to invoke LM recursively
    4. Build up results in variables and return final answer
    """

    def __init__(
        self,
        context: str | dict[str, Any],
        recursive_call_fn: Callable[[str, str], asyncio.Future[str]] | None = None,
        max_timeout_seconds: int = 60,
        debug: bool = False,
    ):
        """
        Initialize REPL environment.

        Args:
            context: The long context (string or dict) available to code
            recursive_call_fn: Async function(text: str, model: str) -> str for recursive calls
            max_timeout_seconds: Maximum execution time per code block
            debug: Enable debug logging
        """
        self.context = context
        self.recursive_call_fn = recursive_call_fn
        self.max_timeout_seconds = max_timeout_seconds
        self.debug = debug
        self.recursive_call_count = 0

        # Build globals/locals for code execution
        self.globals: dict[str, Any] = {
            "context_var": context,
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "sum": sum,
                "max": max,
                "min": min,
                "any": any,
                "all": all,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "print": self._safe_print,
            },
        }
        self.locals: dict[str, Any] = {}
        self.output_buffer: list[str] = []

        # Create dedicated thread pool executor for this REPL (1 worker, timeout-managed)
        self.executor: ThreadPoolExecutor | None = ThreadPoolExecutor(max_workers=1, thread_name_prefix="repl")

    def close(self) -> None:
        """Clean up executor threads."""
        if self.executor:
            self.executor.shutdown(wait=False)  # Don't wait for hanging threads
            self.executor = None

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        self.close()

    def _safe_print(self, *args: Any, **kwargs: Any) -> None:
        """Capture print output safely."""
        sep = kwargs.get("sep", " ")
        output = sep.join(str(arg) for arg in args)
        self.output_buffer.append(output)
        if self.debug:
            logger.debug(f"REPL output: {output}")

    async def execute(self, code: str) -> REPLExecutionResult:
        """
        Execute Python code in the REPL environment.

        Code can:
        - Access `context_var` (the long context)
        - Call `recursive_llm_call(text, model)` for LM recursion
        - Use print() to send output
        - Use standard Python functions (len, str, regex, etc.)

        Args:
            code: Python code to execute

        Returns:
            REPLExecutionResult with success, output, errors, timing
        """
        start_time = time.perf_counter()
        self.output_buffer.clear()

        try:
            # Inject recursive call function if provided
            if self.recursive_call_fn:
                self.globals["recursive_llm_call"] = self.recursive_call_fn

            # Execute with timeout using dedicated executor (1 worker)
            # This avoids thread pool exhaustion and ensures proper cleanup
            if not self.executor:
                self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="repl")

            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self.executor, lambda: exec(code, self.globals, self.locals)
                ),
                timeout=self.max_timeout_seconds,
            )

            execution_time_ms = (time.perf_counter() - start_time) * 1000
            output = "\n".join(self.output_buffer)

            if self.debug:
                logger.debug(
                    f"Code execution successful in {execution_time_ms:.1f}ms. "
                    f"Output length: {len(output)} chars"
                )

            return REPLExecutionResult(
                success=True,
                output=output,
                error=None,
                execution_time_ms=execution_time_ms,
                recursive_calls=self.recursive_call_count,
            )

        except asyncio.TimeoutError:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            error = f"Code execution timed out after {self.max_timeout_seconds}s"
            logger.warning(f"REPL timeout: {error}")
            return REPLExecutionResult(
                success=False,
                output="".join(self.output_buffer),
                error=error,
                execution_time_ms=execution_time_ms,
                recursive_calls=self.recursive_call_count,
            )

        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            error = f"Execution error: {type(e).__name__}: {str(e)}"
            logger.error(f"REPL error: {error}\nCode:\n{code}")
            return REPLExecutionResult(
                success=False,
                output="".join(self.output_buffer),
                error=error,
                execution_time_ms=execution_time_ms,
                recursive_calls=self.recursive_call_count,
            )

    def get_variable(self, name: str) -> Any:
        """Retrieve a variable set in the REPL environment."""
        return self.locals.get(name) or self.globals.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the REPL environment."""
        self.locals[name] = value

    @staticmethod
    def estimate_tokens(text: str, tokens_per_char: float = 0.25) -> int:
        """
        Rough estimate of token count for decision-making.

        OpenAI: ~4 chars per token
        This uses 1 token per 4 chars (0.25 tokens per char)

        Args:
            text: Text to estimate
            tokens_per_char: Conversion factor (default 0.25 for GPT)

        Returns:
            Estimated token count
        """
        return int(len(text) * tokens_per_char)


class PeekStrategy:
    """Strategy: LM peeks at context structure first."""

    @staticmethod
    async def peek(repl: REPLEnvironment, peek_chars: int = 2000) -> str:
        """Show first N characters of context."""
        code = f"""
result = context_var[:{peek_chars}]
print(result)
"""
        result = await repl.execute(code)
        return result.output if result.success else f"[Peek failed: {result.error}]"


class GrepStrategy:
    """Strategy: LM uses regex to narrow context."""

    @staticmethod
    async def grep(repl: REPLEnvironment, pattern: str) -> str:
        """Search context using regex pattern."""
        code = f"""
import re
matches = re.findall(r'{pattern}', context_var)
for i, match in enumerate(matches[:20]):  # Limit output
    print(f"Match {{i+1}}: {{match}}")
if len(matches) > 20:
    print(f"... and {{len(matches) - 20}} more matches")
"""
        result = await repl.execute(code)
        return result.output if result.success else f"[Grep failed: {result.error}]"


class PartitionStrategy:
    """Strategy: LM partitions context and recurses."""

    @staticmethod
    async def partition(repl: REPLEnvironment, chunk_size: int = 50000) -> list[str]:
        """Partition context into chunks."""
        code = f"""
chunk_size = {chunk_size}
chunks = []
for i in range(0, len(context_var), chunk_size):
    chunks.append(context_var[i:i+chunk_size])
print(f"Partitioned into {{len(chunks)}} chunks of ~{{chunk_size}} chars each")
"""
        result = await repl.execute(code)
        if result.success:
            return repl.get_variable("chunks") or []
        return []
