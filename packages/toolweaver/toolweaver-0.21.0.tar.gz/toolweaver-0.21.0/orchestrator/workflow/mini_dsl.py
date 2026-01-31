"""
Lean skill composition DSL (Differentiator #4).

Supports sequential and fan-out execution of skills/capabilities with a
minimal YAML/JSON structure. Gated by COMPOSITION_ENABLED.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast


def _get_env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class DSLExecutionResult:
    success: bool
    results: dict[str, Any] = field(default_factory=dict)
    final_output: Any = None
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DSLStep:
    name: str
    skill: str
    capability: str
    mapping: dict[str, Any] = field(default_factory=dict)


@dataclass
class FanoutStep:
    name: str
    branches: list[DSLStep]


class MiniDSLExecutor:
    """Execute the lean composition DSL with optional fan-out."""

    def __init__(
        self,
        skill_resolver: Callable[[str, str], Callable[..., Any]] | None = None,
        enabled: bool | None = None,
    ):
        self.enabled = (
            enabled if enabled is not None else _get_env_bool("COMPOSITION_ENABLED", False)
        )
        self.skill_resolver = skill_resolver or self._default_resolver

    async def _default_resolver(self, skill: str, capability: str) -> Callable[..., Any]:
        raise ValueError(f"No resolver provided for {skill}.{capability}")

    async def run(
        self, spec: dict[str, Any], context: dict[str, Any] | None = None
    ) -> DSLExecutionResult:
        if not self.enabled:
            return DSLExecutionResult(
                success=False,
                error="Composition disabled (COMPOSITION_ENABLED=false)",
            )

        steps = _parse_workflow(spec)
        if not steps:
            return DSLExecutionResult(success=False, error="Workflow has no steps")

        results: dict[str, Any] = {}
        events: list[dict[str, Any]] = []
        prev_output: Any = context or {}

        for idx, step in enumerate(steps):
            if isinstance(step, FanoutStep):
                branch_outputs = []
                for branch in step.branches:
                    params = _render_mapping(branch.mapping, prev_output, results, context)
                    try:
                        callable_fn = await self._resolve(branch.skill, branch.capability)
                        output = await _invoke(callable_fn, params)
                        branch_outputs.append(output)
                        events.append({"type": "progress", "step": branch.name, "result": output})
                    except Exception as exc:  # noqa: BLE001
                        return DSLExecutionResult(
                            success=False,
                            results=results,
                            final_output=None,
                            error=str(exc),
                            events=events,
                        )
                results[step.name or f"fanout_{idx}"] = branch_outputs
                prev_output = branch_outputs[-1] if branch_outputs else prev_output
            else:
                params = _render_mapping(step.mapping, prev_output, results, context)
                try:
                    callable_fn = await self._resolve(step.skill, step.capability)
                    output = await _invoke(callable_fn, params)
                    results[step.name] = output
                    prev_output = output
                    events.append({"type": "progress", "step": step.name, "result": output})
                except Exception as exc:  # noqa: BLE001
                    return DSLExecutionResult(
                        success=False,
                        results=results,
                        final_output=None,
                        error=str(exc),
                        events=events,
                    )

        return DSLExecutionResult(
            success=True,
            results=results,
            final_output=prev_output,
            events=events,
        )

    async def _resolve(self, skill: str, capability: str) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(self.skill_resolver):
            return cast(Callable[..., Any], await self.skill_resolver(skill, capability))
        return cast(Callable[..., Any], self.skill_resolver(skill, capability))


def _parse_workflow(spec: dict[str, Any]) -> list[Any]:
    steps_spec = spec.get("steps") if isinstance(spec, dict) else None
    if not steps_spec:
        return []

    parsed: list[Any] = []
    for idx, raw in enumerate(steps_spec):
        if "fanout" in raw:
            branches = [
                DSLStep(
                    name=branch.get("name") or f"fanout_{idx}_b{b_idx}",
                    skill=branch["skill"],
                    capability=branch["capability"],
                    mapping=branch.get("map", {}),
                )
                for b_idx, branch in enumerate(raw["fanout"])
            ]
            parsed.append(FanoutStep(name=raw.get("name") or f"fanout_{idx}", branches=branches))
        else:
            parsed.append(
                DSLStep(
                    name=raw.get("name") or f"step_{idx}",
                    skill=raw["skill"],
                    capability=raw["capability"],
                    mapping=raw.get("map", {}),
                )
            )
    return parsed


def _render_mapping(
    mapping: dict[str, Any],
    prev_output: Any,
    results: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rendered: dict[str, Any] = {}
    for key, value in mapping.items():
        rendered[key] = _render_value(value, prev_output, results, context or {})
    return rendered


def _render_value(
    value: Any, prev_output: Any, results: dict[str, Any], context: dict[str, Any]
) -> Any:
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        expr = value[2:-2].strip()
        return _resolve_expr(expr, prev_output, results, context)
    return value


def _resolve_expr(
    expr: str, prev_output: Any, results: dict[str, Any], context: dict[str, Any]
) -> Any:
    if expr.startswith("prev"):
        return _walk(prev_output, expr.split(".")[1:])
    if expr.startswith("results."):
        parts = expr.split(".")
        step_name = parts[1] if len(parts) > 1 else None
        if step_name and step_name in results:
            return _walk(results[step_name], parts[2:])
    if expr.startswith("context."):
        return _walk(context, expr.split(".")[1:])
    return None


def _walk(obj: Any, parts: list[str]) -> Any:
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _ensure_coroutine(fn: Callable[..., Any]) -> Callable[..., Any]:
    if asyncio.iscoroutinefunction(fn):
        return fn

    async def wrapper(**kwargs: Any) -> Any:
        return fn(**kwargs)

    return wrapper


async def _invoke(fn: Callable[..., Any], params: dict[str, Any]) -> Any:
    coro_fn = _ensure_coroutine(fn)
    return await coro_fn(**params)
