"""
RLM Planner Integration for Task Planning Skill.

Bridges task planning with RLM infrastructure:
- Decides between traditional and RLM planning
- Generates RLM-compatible plans with peek/grep/partition steps
- Integrates with context analyzer and REPL environment

Based on: Recursive Language Models (Zhang et al., Dec 2025)
"""

import json
import logging
import os
from typing import Any

from orchestrator.skills.task_planning.context_analyzer import analyze_context
from orchestrator.tools.repl_environment import (
    GrepStrategy,
    PartitionStrategy,
    PeekStrategy,
    REPLEnvironment,
)

logger = logging.getLogger(__name__)


def should_use_rlm(task: str, context: str | dict[str, Any]) -> tuple[bool, str]:
    """
    Determine if RLM should be used for this task.

    Returns:
        (use_rlm, reason)
    """
    rlm_mode = os.getenv("RLM_MODE", "adaptive")
    analysis = analyze_context(task, context, rlm_mode)
    return analysis.use_rlm, analysis.reason


def generate_traditional_plan(task: str, context: str | dict[str, Any]) -> dict[str, Any]:
    """
    Generate a traditional (non-RLM) execution plan.

    This is the baseline - direct approach without recursive decomposition.
    """
    context_str = context if isinstance(context, str) else json.dumps(context)

    return {
        "strategy": "traditional",
        "task": task,
        "context_size_bytes": len(context_str.encode("utf-8")),
        "steps": [
            {
                "id": 1,
                "tool": "direct_llm_call",
                "description": "Call LLM directly with full context",
                "params": {
                    "task": task,
                    "context": context_str[:10000],  # Truncate for safety
                },
            }
        ],
        "execution_order": [[1]],
        "estimated_recursion_depth": 0,
    }


def generate_rlm_plan(
    task: str,
    context: str | dict[str, Any],
    strategy_hint: str | None = None,
) -> dict[str, Any]:
    """
    Generate an RLM-compatible execution plan.

    Plan structure:
    1. Peek: LM examines context structure
    2. Strategy-specific steps: grep, partition, or direct
    3. Recursion: Recursive LM calls on chunks (if needed)
    4. Aggregation: Combine results

    Args:
        task: Task description
        context: The context
        strategy_hint: Override strategy (peek, grep, partition, programmatic)

    Returns:
        RLM-compatible plan
    """
    context_str = context if isinstance(context, str) else json.dumps(context)
    analysis = analyze_context(task, context_str)

    strategy = strategy_hint or analysis.suggested_strategy.value
    chunk_size = analysis.suggested_chunk_size or 50000

    plan: dict[str, Any] = {
        "strategy": "rlm",
        "task": task,
        "context_size_bytes": len(context_str.encode("utf-8")),
        "estimated_tokens": analysis.estimated_tokens,
        "task_complexity": analysis.task_complexity,
        "rlm_strategy": strategy,
        "estimated_recursion_depth": analysis.estimated_recursion_depth,
        "steps": [],
        "execution_order": [],
    }

    step_id = 1

    # Step 1: Peek (always start here to understand structure)
    plan["steps"].append(
        {
            "id": step_id,
            "tool": "rlm_peek",
            "description": "LM peeks at context structure (first 2000 chars)",
            "params": {
                "peek_chars": 2000,
            },
        }
    )
    peek_step_id = step_id
    step_id += 1

    # Step 2-N: Strategy-specific steps
    if strategy == "grep":
        plan["steps"].append(
            {
                "id": step_id,
                "tool": "rlm_grep",
                "description": "LM uses regex to narrow search space",
                "params": {
                    "pattern": "<generated dynamically by LM>",  # LM will decide
                },
                "depends_on": [peek_step_id],
            }
        )
        plan["execution_order"].append([peek_step_id])
        plan["execution_order"].append([step_id])

    elif strategy == "partition":
        partition_step_id = step_id
        plan["steps"].append(
            {
                "id": step_id,
                "tool": "rlm_partition",
                "description": f"Partition context into {chunk_size}-char chunks",
                "params": {
                    "chunk_size": chunk_size,
                },
                "depends_on": [peek_step_id],
            }
        )
        step_id += 1

        # Recursive calls on each chunk
        for chunk_idx in range(analysis.estimated_recursion_depth):
            plan["steps"].append(
                {
                    "id": step_id,
                    "tool": "recursive_llm_call",
                    "description": f"Recursive call {chunk_idx + 1} on context chunk",
                    "params": {
                        "chunk_index": chunk_idx,
                        "task": task,
                    },
                    "depends_on": [partition_step_id],
                }
            )
            step_id += 1

        # Aggregation
        plan["steps"].append(
            {
                "id": step_id,
                "tool": "aggregate_results",
                "description": "Aggregate results from recursive calls",
                "params": {},
                "depends_on": list(range(partition_step_id + 1, step_id)),
            }
        )
        plan["execution_order"].append([peek_step_id])
        plan["execution_order"].append([partition_step_id])
        plan["execution_order"].append(list(range(partition_step_id + 1, step_id)))
        plan["execution_order"].append([step_id])

    elif strategy == "programmatic":
        plan["steps"].append(
            {
                "id": step_id,
                "tool": "rlm_programmatic",
                "description": "Execute programmatic task directly (git diff, math, etc)",
                "params": {
                    "task": task,
                },
                "depends_on": [peek_step_id],
            }
        )
        plan["execution_order"].append([peek_step_id])
        plan["execution_order"].append([step_id])

    else:  # direct/summarize
        plan["steps"].append(
            {
                "id": step_id,
                "tool": "recursive_llm_call",
                "description": "Recursive LM call with structured context",
                "params": {
                    "task": task,
                    "context_size": analysis.estimated_tokens,
                },
                "depends_on": [peek_step_id],
            }
        )
        plan["execution_order"].append([peek_step_id])
        plan["execution_order"].append([step_id])

    return plan


async def execute_rlm_plan_step(
    step: dict[str, Any],
    repl: REPLEnvironment,
    previous_results: dict[int, Any],
) -> Any:
    """
    Execute a single step in an RLM plan.

    Args:
        step: Plan step to execute
        repl: REPL environment
        previous_results: Results from previous steps

    Returns:
        Step result
    """
    tool = step.get("tool", "")
    params = step.get("params", {})

    if tool == "rlm_peek":
        return await PeekStrategy.peek(
            repl,
            peek_chars=params.get("peek_chars", 2000),
        )

    elif tool == "rlm_grep":
        # In real execution, the pattern would come from LM output
        pattern = params.get("pattern", ".*")
        return await GrepStrategy.grep(repl, pattern)

    elif tool == "rlm_partition":
        chunks = await PartitionStrategy.partition(
            repl,
            chunk_size=params.get("chunk_size", 50000),
        )
        return {
            "chunks": chunks,
            "count": len(chunks),
        }

    elif tool == "recursive_llm_call":
        # Placeholder - in real implementation, call LLM recursively
        return {
            "status": "placeholder",
            "message": "Recursive LM call would execute here",
        }

    elif tool == "aggregate_results":
        # Combine results from previous steps
        return {
            "aggregated": True,
            "sources": params.get("sources", []),
        }

    elif tool == "rlm_programmatic":
        # Execute programmatic task
        code = params.get("code", "")
        if code:
            result = await repl.execute(code)
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        return {"error": "No code provided"}

    elif tool == "direct_llm_call":
        return {
            "status": "placeholder",
            "message": "Direct LM call would execute here",
        }

    else:
        return {"error": f"Unknown tool: {tool}"}


def select_planner(task: str, context: str | dict[str, Any]) -> Any:
    """
    Select appropriate planner (traditional or RLM) based on analysis.

    Returns appropriate planner function or None if no preference.
    """
    use_rlm, reason = should_use_rlm(task, context)

    logger.info(f"Planner selection: RLM={use_rlm}, reason={reason}")

    if use_rlm:
        return "rlm"
    else:
        return "traditional"
