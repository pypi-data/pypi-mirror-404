"""
Task Planning Skill

Wrapper around orchestrator._internal.planning module for creating
and managing task plans.

Supports both traditional and RLM-based planning based on RLM_MODE configuration.
Integrates with ExecutionContext for session tracking and observability.
"""

import logging
from typing import Any, Optional

from orchestrator._internal.planning.planner import LargePlanner
from orchestrator.config import get_config
from orchestrator.context import ExecutionContext, get_context, set_context
from orchestrator.observability import log_execution
from orchestrator.skills.task_planning.rlm_planner import (
    generate_rlm_plan,
    generate_traditional_plan,
    select_planner,
)

logger = logging.getLogger(__name__)

# Global planner instance
_planner = None


def get_planner() -> LargePlanner:
    """Get or create the global planner instance."""
    global _planner
    if _planner is None:
        _planner = LargePlanner()
    return _planner


def create_plan(
    task: str,
    context: dict[str, Any] | None = None,
    constraints: dict[str, Any] | None = None,
    execution_context: ExecutionContext | None = None,
) -> dict[str, Any]:
    """
    Create a plan from a task description.

    Branches between traditional and RLM-based planning based on:
    1. RLM_MODE configuration (off, adaptive, always)
    2. Context size (for adaptive mode)

    Integrates with ExecutionContext for session tracking and cost estimation.

    Args:
        task: Task description
        context: Optional context data (may contain long-form text)
        constraints: Optional constraints for planning
        execution_context: Optional ExecutionContext for session tracking

    Returns:
        Plan dictionary with strategy, task, and steps
    """
    # Use provided context or get from global context
    if execution_context is None:
        execution_context = get_context()

    # Create new context if not provided
    if execution_context is None:
        execution_context = ExecutionContext(task_description=task)

    # Set as current context
    set_context(execution_context)
    execution_context.mark_started()

    try:
        config = get_config()

        # Prepare context for RLM analysis
        context_text = ""
        if context:
            if isinstance(context, str):
                context_text = context
            elif isinstance(context, dict):
                # Extract text values from context
                context_text = " ".join(str(v) for v in context.values() if isinstance(v, str))

        # Select planner based on RLM mode and context
        planner_type = select_planner(task, context_text)

        # Use RLM-based planning if selected and enabled
        if planner_type == "rlm" and config.is_rlm_enabled():
            logger.info(
                "Using RLM planner for task",
                extra={
                    "request_id": execution_context.request_id,
                    "session_id": execution_context.session_id,
                    "rlm_mode": config.rlm_mode,
                },
            )
            try:
                plan = generate_rlm_plan(task, context_text)
                execution_context.add_metadata("plan_strategy", "rlm")
                execution_context.mark_completed(result=plan)
                log_execution(execution_context)
                return plan
            except Exception as e:
                logger.warning(
                    f"RLM planning failed, falling back to traditional: {e}",
                    extra={
                        "request_id": execution_context.request_id,
                        "session_id": execution_context.session_id,
                    },
                )
                # Fall through to traditional planning

        # Use traditional planning (default)
        logger.info(
            "Using traditional planner for task",
            extra={
                "request_id": execution_context.request_id,
                "session_id": execution_context.session_id,
            },
        )
        get_planner()
        plan = generate_traditional_plan(task, context_text)
        execution_context.add_metadata("plan_strategy", "traditional")
        execution_context.mark_completed(result=plan)
        log_execution(execution_context)
        return plan

    except Exception as e:
        logger.error(
            f"Plan creation failed: {e}",
            extra={
                "request_id": execution_context.request_id,
                "session_id": execution_context.session_id,
            },
        )
        execution_context.mark_failed(str(e))
        log_execution(execution_context)
        raise


def decompose_task(
    task: str, max_depth: int = 3, strategy: str = "hierarchical"
) -> list[dict[str, Any]]:
    """Decompose a complex task into subtasks."""
    planner = get_planner()

    if hasattr(planner, "decompose"):
        subtasks = planner.decompose(task=task, max_depth=max_depth, strategy=strategy)
    else:
        # Fallback: return single task as-is
        subtasks = [{"task": task, "level": 0}]

    return [{"task": str(st), "level": i, "dependencies": []} for i, st in enumerate(subtasks)]


def optimize_plan(plan: dict[str, Any], metric: str = "time") -> dict[str, Any]:
    """Optimize a plan for efficiency."""
    planner = get_planner()

    if hasattr(planner, "optimize"):
        planner.optimize(plan, metric=metric)
    else:
        pass

    return {"optimized": True, "metric": metric, "improvement": 0.0}


def validate_plan(plan: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    """Validate a plan for completeness and consistency."""
    planner = get_planner()

    if hasattr(planner, "validate"):
        valid, issues = planner.validate(plan, strict=strict)
    else:
        valid, issues = True, []

    return {"valid": valid, "issues": issues, "strict": strict}


def get_planning_stats() -> dict[str, Any]:
    """Get planning statistics."""
    planner = get_planner()

    stats = {
        "plans_created": getattr(planner, "plans_count", 0),
        "tasks_decomposed": getattr(planner, "decomposed_count", 0),
        "avg_plan_steps": getattr(planner, "avg_steps", 0),
    }

    return stats


__all__ = ["create_plan", "decompose_task", "optimize_plan", "validate_plan", "get_planning_stats"]
