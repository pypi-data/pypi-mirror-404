"""
Agentic Executor - End-to-end loop for Claude SDK + ToolWeaver

Implements the complete agentic workflow:
1. Planning: Use OrchestratorBackend (Claude SDK) to generate tool calls
2. Execution: Execute tool calls via ToolWeaver
3. Feedback: Return results to orchestrator for next iteration
4. Iteration: Repeat until task complete or max iterations reached

Architecture:
    AgenticExecutor orchestrates the loop between planning (OrchestratorBackend)
    and execution (ToolWeaver tool_executor). It manages:
    - Conversation history across turns
    - Error recovery (pass errors to planner)
    - Iteration limits and termination conditions
    - Tool result formatting

Usage:
    from orchestrator.adapters.orchestrator_interface import OrchestratorConfig
    from orchestrator.adapters.claude_orchestrator import ClaudeOrchestrator
    from orchestrator.adapters.agentic_executor import AgenticExecutor

    # Setup
    config = OrchestratorConfig(model="claude-3-5-sonnet-20241022")
    orchestrator = ClaudeOrchestrator(config)
    executor = AgenticExecutor(orchestrator)

    # Register tools
    tools = [
        ToolSchema(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "location": {"type": "string", "description": "City name"}
            }
        )
    ]
    executor.register_tools(tools)

    # Execute task
    result = await executor.execute_task(
        "What's the weather in San Francisco?",
        max_iterations=5
    )
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    PlanResult,
    ToolCall,
    ToolSchema,
)
from orchestrator.observability import MonitoringHooks

logger = logging.getLogger(__name__)


@dataclass
class AgenticResult:
    """Result from agentic execution."""

    success: bool
    """Whether task completed successfully."""

    final_response: str
    """Final text response from orchestrator."""

    iterations: int
    """Number of planning iterations."""

    tool_calls: list[ToolCall]
    """All tool calls made during execution."""

    tool_results: list[dict[str, Any]]
    """Results from all tool executions."""

    error: str | None = None
    """Error message if execution failed."""


class AgenticExecutor:
    """
    Agentic executor implementing plan → execute → feedback loop.

    Orchestrates between planning (OrchestratorBackend) and execution (ToolWeaver).
    Manages conversation history, error recovery, and iteration control.
    """

    def __init__(
        self,
        orchestrator: OrchestratorBackend,
        system_prompt: str | None = None,
    ):
        """
        Initialize agentic executor.

        Args:
            orchestrator: Backend for planning (Claude, OpenAI, etc.)
            system_prompt: Optional system instructions for orchestrator
        """
        self.orchestrator = orchestrator
        self.system_prompt = system_prompt or (
            "You are a helpful AI assistant with access to tools. "
            "Use the tools to complete the user's task. "
            "When you have enough information, provide a final answer."
        )

        # Execution state
        self._all_tool_calls: list[ToolCall] = []
        self._all_tool_results: list[dict[str, Any]] = []
        self._iteration_count = 0

    def register_tools(self, tools: list[ToolSchema]) -> None:
        """
        Register tools with the orchestrator.

        Args:
            tools: List of tool schemas to make available
        """
        logger.info(f"Registering {len(tools)} tools with orchestrator")
        self.orchestrator.register_tools(tools)

    async def execute_task(
        self,
        user_message: str,
        max_iterations: int = 10,
        tool_timeout: int = 30,
    ) -> AgenticResult:
        """
        Execute a task using agentic loop.

        Flow:
            1. Send user message to orchestrator
            2. Get plan with tool calls
            3. Execute tool calls via ToolWeaver
            4. Return results to orchestrator
            5. Repeat until done or max iterations

        Args:
            user_message: User's task/question
            max_iterations: Maximum planning iterations
            tool_timeout: Timeout for each tool execution (seconds)

        Returns:
            AgenticResult with execution summary

        Example:
            result = await executor.execute_task(
                "Find the weather in Paris and convert to Fahrenheit",
                max_iterations=5
            )
            print(result.final_response)
        """
        start_time = time.perf_counter()
        logger.info(f"Starting agentic execution: {user_message[:100]}...")
        MonitoringHooks.record_agent_start(user_message)

        # Reset state
        self._all_tool_calls = []
        self._all_tool_results = []
        self._iteration_count = 0

        try:
            # Initial planning
            plan_result = self.orchestrator.plan(
                user_message=user_message,
                system_prompt=self.system_prompt,
            )

            # Agentic loop
            while self._iteration_count < max_iterations:
                self._iteration_count += 1
                logger.info(f"Iteration {self._iteration_count}/{max_iterations}")
                MonitoringHooks.record_agent_step(
                    self._iteration_count,
                    "plan",
                    {"stop_reason": plan_result.stop_reason},
                )

                # Check if orchestrator is done
                if plan_result.stop_reason in ["end_turn", "stop_sequence"]:
                    logger.info(f"Orchestrator finished: {plan_result.stop_reason}")
                    duration = (time.perf_counter() - start_time) * 1000
                    MonitoringHooks.record_agent_completion(
                        success=True,
                        iterations=self._iteration_count,
                        duration_ms=duration,
                    )
                    return AgenticResult(
                        success=True,
                        final_response=plan_result.reasoning or "Task completed",
                        iterations=self._iteration_count,
                        tool_calls=self._all_tool_calls,
                        tool_results=self._all_tool_results,
                    )

                # Execute tool calls if any
                if not plan_result.tool_calls:
                    logger.info("No tool calls in plan, ending loop")
                    duration = (time.perf_counter() - start_time) * 1000
                    MonitoringHooks.record_agent_completion(
                        success=True,
                        iterations=self._iteration_count,
                        duration_ms=duration,
                    )
                    return AgenticResult(
                        success=True,
                        final_response=plan_result.reasoning or "Task completed",
                        iterations=self._iteration_count,
                        tool_calls=self._all_tool_calls,
                        tool_results=self._all_tool_results,
                    )

                # Execute tools and collect results
                logger.info(f"Executing {len(plan_result.tool_calls)} tool calls")
                tool_results = await self._execute_tools(
                    plan_result.tool_calls,
                    tool_timeout,
                )

                # Track all calls and results
                self._all_tool_calls.extend(plan_result.tool_calls)
                self._all_tool_results.extend(tool_results)

                # Send results back to orchestrator for next iteration
                plan_result = await self._send_tool_results(tool_results)

            # Max iterations reached
            logger.warning(f"Max iterations ({max_iterations}) reached")
            duration = (time.perf_counter() - start_time) * 1000
            MonitoringHooks.record_agent_completion(
                success=False,
                iterations=self._iteration_count,
                duration_ms=duration,
                error="max_iterations_reached",
            )
            return AgenticResult(
                success=False,
                final_response=f"Maximum iterations ({max_iterations}) reached",
                iterations=self._iteration_count,
                tool_calls=self._all_tool_calls,
                tool_results=self._all_tool_results,
                error="max_iterations_reached",
            )

        except Exception as e:
            logger.error(f"Agentic execution failed: {e}", exc_info=True)
            duration = (time.perf_counter() - start_time) * 1000
            MonitoringHooks.record_agent_completion(
                success=False,
                iterations=self._iteration_count,
                duration_ms=duration,
                error=str(e),
            )
            return AgenticResult(
                success=False,
                final_response="",
                iterations=self._iteration_count,
                tool_calls=self._all_tool_calls,
                tool_results=self._all_tool_results,
                error=str(e),
            )

    async def _execute_tools(
        self,
        tool_calls: list[ToolCall],
        timeout: int,
    ) -> list[dict[str, Any]]:
        """
        Execute tool calls via ToolWeaver.

        Args:
            tool_calls: List of tool calls to execute
            timeout: Timeout for each tool

        Returns:
            List of tool results with success/error information
        """
        from orchestrator.tools.tool_executor import call_tool

        results = []

        for tool_call in tool_calls:
            logger.info(f"Executing tool: {tool_call.tool_name}")
            logger.debug(f"Parameters: {tool_call.parameters}")
            tool_start = time.perf_counter()

            try:
                # Execute via ToolWeaver
                # Assume "default" server for function-based tools
                result = await call_tool(
                    server="default",
                    tool_name=tool_call.tool_name,
                    parameters=tool_call.parameters,
                    timeout=timeout,
                )
                tool_duration = (time.perf_counter() - tool_start) * 1000
                MonitoringHooks.record_tool_call(
                    tool_call.tool_name, tool_duration, True
                )

                # Success result
                tool_result = {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.tool_name,
                    "success": True,
                    "result": result,
                    "duration_ms": tool_duration,
                }
                logger.info(f"Tool {tool_call.tool_name} succeeded")

            except Exception as e:
                tool_duration = (time.perf_counter() - tool_start) * 1000
                MonitoringHooks.record_tool_call(
                    tool_call.tool_name, tool_duration, False, str(e)
                )

                # Error result - pass to orchestrator for recovery
                logger.warning(f"Tool {tool_call.tool_name} failed: {e}")
                tool_result = {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.tool_name,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": tool_duration,
                }

            results.append(tool_result)

        return results

    async def _send_tool_results(
        self,
        tool_results: list[dict[str, Any]],
    ) -> PlanResult:
        """
        Send tool results back to orchestrator.

        Args:
            tool_results: Results from tool execution

        Returns:
            Next plan from orchestrator
        """
        logger.info(f"Sending {len(tool_results)} tool results to orchestrator")

        # Add tool results to conversation
        for result in tool_results:
            tool_call_id = result.get("tool_call_id", "")

            if result.get("success", False):
                # Success: send result
                result_data = result.get("result", {})
                self.orchestrator.add_tool_result(
                    tool_call_id=tool_call_id,
                    result=result_data,
                    is_error=False,
                )
            else:
                # Error: send error message
                error_msg = result.get("error", "Unknown error")
                self.orchestrator.add_tool_result(
                    tool_call_id=tool_call_id,
                    result=f"Error: {error_msg}",
                    is_error=True,
                )

        # Get next plan (orchestrator will use conversation history)
        plan_result = self.orchestrator.plan(
            user_message="",  # Empty, orchestrator uses history
            system_prompt=self.system_prompt,
        )

        return plan_result

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """
        Get full conversation history from orchestrator.

        Returns:
            List of messages in conversation

        Example:
            history = executor.get_conversation_history()
            for msg in history:
                print(f"{msg['role']}: {msg.get('content', msg)}")
        """
        return self.orchestrator.get_conversation_history()

    def clear_history(self) -> None:
        """Clear conversation history and reset execution state."""
        logger.info("Clearing conversation history and execution state")
        self.orchestrator.clear_conversation_history()
        self._all_tool_calls = []
        self._all_tool_results = []
        self._iteration_count = 0
