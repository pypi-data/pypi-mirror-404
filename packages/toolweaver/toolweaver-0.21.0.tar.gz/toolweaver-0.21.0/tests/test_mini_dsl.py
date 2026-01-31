from collections.abc import Callable, Generator
from typing import Any

import pytest

from orchestrator.workflow.mini_dsl import MiniDSLExecutor


@pytest.fixture(autouse=True)
def reset_env(monkeypatch: Any) -> Generator[None, None, None]:
    # Default disabled unless explicitly enabled in tests
    monkeypatch.delenv("COMPOSITION_ENABLED", raising=False)
    yield


@pytest.mark.asyncio
async def test_gating_disabled(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "false")
    executor = MiniDSLExecutor()
    result = await executor.run({"steps": [{"skill": "s", "capability": "c"}]})
    assert not result.success
    assert "disabled" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_sequential_execution_with_prev_templating(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "true")

    async def step1(value: int) -> dict[str, int]:
        return {"double": value * 2}

    async def step2(val: int) -> dict[str, int]:
        return {"final": val + 1}

    def resolver(skill: str, capability: str) -> Callable[..., Any]:
        mapping: dict[tuple[str, str], Callable[..., Any]] = {("math", "double"): step1, ("math", "increment"): step2}
        return mapping[(skill, capability)]

    spec = {
        "steps": [
            {"name": "first", "skill": "math", "capability": "double", "map": {"value": 3}},
            {
                "name": "second",
                "skill": "math",
                "capability": "increment",
                "map": {"val": "{{prev.double}}"},
            },
        ]
    }

    executor = MiniDSLExecutor(skill_resolver=resolver)
    result = await executor.run(spec)

    assert result.success
    assert result.final_output == {"final": 7}
    assert result.results["first"] == {"double": 6}
    assert result.results["second"] == {"final": 7}


@pytest.mark.asyncio
async def test_results_reference(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "true")

    async def first() -> dict[str, Any]:
        return {"name": "alice", "score": 10}

    async def second(username: str) -> dict[str, str]:
        return {"greeting": f"hi {username}"}

    def resolver(skill: str, capability: str) -> Callable[..., Any]:
        mapping: dict[tuple[str, str], Callable[..., Any]] = {("alpha", "one"): first, ("alpha", "two"): second}
        return mapping[(skill, capability)]

    spec = {
        "steps": [
            {"name": "s1", "skill": "alpha", "capability": "one", "map": {}},
            {
                "name": "s2",
                "skill": "alpha",
                "capability": "two",
                "map": {"username": "{{results.s1.name}}"},
            },
        ]
    }

    executor = MiniDSLExecutor(skill_resolver=resolver)
    result = await executor.run(spec)

    assert result.success
    assert result.final_output["greeting"] == "hi alice"


@pytest.mark.asyncio
async def test_fanout_execution(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "true")

    async def upper(text: str) -> dict[str, str]:
        return {"text": text.upper()}

    async def lower(text: str) -> dict[str, str]:
        return {"text": text.lower()}

    def resolver(skill: str, capability: str) -> Callable[..., Any]:
        mapping: dict[tuple[str, str], Callable[..., Any]] = {("text", "upper"): upper, ("text", "lower"): lower}
        return mapping[(skill, capability)]

    spec = {
        "steps": [
            {
                "name": "fan",
                "fanout": [
                    {
                        "name": "up",
                        "skill": "text",
                        "capability": "upper",
                        "map": {"text": "Hello"},
                    },
                    {
                        "name": "low",
                        "skill": "text",
                        "capability": "lower",
                        "map": {"text": "Hello"},
                    },
                ],
            }
        ]
    }

    executor = MiniDSLExecutor(skill_resolver=resolver)
    result = await executor.run(spec)

    assert result.success
    assert len(result.results["fan"]) == 2
    assert result.results["fan"][0]["text"] == "HELLO"
    assert result.results["fan"][1]["text"] == "hello"


@pytest.mark.asyncio
async def test_error_stops_execution(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "true")

    async def ok() -> dict[str, int]:
        return {"a": 1}

    async def boom() -> dict[str, int]:
        raise RuntimeError("boom")

    def resolver(skill: str, capability: str) -> Callable[..., Any]:
        mapping: dict[tuple[str, str], Callable[..., Any]] = {("s", "ok"): ok, ("s", "boom"): boom}
        return mapping[(skill, capability)]

    spec = {
        "steps": [
            {"name": "one", "skill": "s", "capability": "ok", "map": {}},
            {"name": "two", "skill": "s", "capability": "boom", "map": {}},
            {"name": "three", "skill": "s", "capability": "ok", "map": {}},
        ]
    }

    executor = MiniDSLExecutor(skill_resolver=resolver)
    result = await executor.run(spec)

    assert not result.success
    assert "boom" in (result.error or "")
    assert "three" not in result.results


@pytest.mark.asyncio
async def test_empty_steps(monkeypatch: Any) -> None:
    monkeypatch.setenv("COMPOSITION_ENABLED", "true")

    def bad_resolver(skill: str, capability: str) -> Callable[..., Any]:
        return lambda: None

    executor = MiniDSLExecutor(skill_resolver=bad_resolver)
    result = await executor.run({"steps": []})
    assert not result.success
    assert "no steps" in (result.error or "").lower()
