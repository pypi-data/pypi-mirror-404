import asyncio
import os
from collections.abc import Generator
from typing import Any, cast
from unittest.mock import patch

import pytest

from orchestrator._internal.infra.mcp_client import MCPClientShim


@pytest.fixture(autouse=True)
def use_local_registry() -> Generator[None, None, None]:
    """Ensure all tests use local registry instead of redis."""
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        yield


@pytest.mark.asyncio
async def test_mcp_idempotency_cache_ttl_and_lru() -> None:
    client = MCPClientShim()

    async def worker(payload: dict[str, Any]) -> Any:
        return payload["x"]

    client.tool_map = cast(dict[str, Any], {"echo": worker})

    # First call caches
    result1 = cast(Any, await client.call_tool("echo", {"x": 1}, idempotency_key="k1"))
    assert result1 == 1

    # Cached
    result2 = cast(Any, await client.call_tool("echo", {"x": 2}, idempotency_key="k1"))
    assert result2 == 1


@pytest.mark.asyncio
async def test_mcp_retry_then_success() -> None:
    calls = {"count": 0}

    async def flaky(payload: dict[str, Any]) -> str:
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("fail once")
        return "ok"

    client = MCPClientShim(max_retries=2, retry_backoff_s=0.01)
    client.tool_map = cast(dict[str, Any], {"flaky": flaky})

    result = cast(Any, await client.call_tool("flaky", {}))
    assert result == "ok"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_mcp_circuit_opens_after_failures() -> None:
    async def always_fail(payload: dict[str, Any]) -> None:
        raise RuntimeError("boom")

    client = MCPClientShim(max_retries=0, circuit_breaker_threshold=1, circuit_reset_s=1)
    client.tool_map = cast(dict[str, Any], {"bad": always_fail})

    with pytest.raises(RuntimeError):
        await client.call_tool("bad", {})

    # Circuit should be open now
    with pytest.raises(RuntimeError, match="circuit open"):
        await client.call_tool("bad", {})

    # Wait for reset and ensure it attempts again
    await asyncio.sleep(1.05)
    with pytest.raises(RuntimeError):
        await client.call_tool("bad", {})


@pytest.mark.asyncio
async def test_mcp_observer_events() -> None:
    events = []

    def observer(evt: str, data: dict[str, Any]) -> None:
        events.append((evt, data))

    async def worker(payload: dict[str, Any]) -> str:
        return "ok"

    client = MCPClientShim(observer=observer)
    client.tool_map = cast(dict[str, Any], {"ok": worker})

    await client.call_tool("ok", {}, idempotency_key="observer-1")

    assert any(e[0] == "mcp.start" for e in events)
    assert any(e[0] == "mcp.complete" and e[1].get("success") is True for e in events)
    # cache hit should emit on second call
    await client.call_tool("ok", {}, idempotency_key="observer-1")
    assert any(e[0] == "mcp.cache_hit" for e in events)


@pytest.mark.asyncio
async def test_mcp_streaming_emits_chunks_and_events() -> None:
    events = []

    def observer(evt: str, data: dict[str, Any]) -> None:
        events.append((evt, data))

    async def stream_worker(payload: dict[str, Any]) -> Any:
        for i in range(3):
            await asyncio.sleep(0)
            yield f"chunk-{i}"

    client = MCPClientShim(observer=observer)
    client.tool_map = cast(dict[str, Any], {"stream": stream_worker})

    chunks: list[str] = []
    async for chunk in client.call_tool_stream("stream", {}, chunk_timeout=1):
        chunks.append(chunk)

    assert chunks == ["chunk-0", "chunk-1", "chunk-2"]
    assert any(e[0] == "mcp.stream.start" for e in events)
    assert any(e[0] == "mcp.stream.chunk" for e in events)
    assert any(e[0] == "mcp.stream.complete" and e[1].get("success") is True for e in events)


@pytest.mark.asyncio
async def test_mcp_streaming_retries_on_chunk_timeout() -> None:
    calls = {"attempt": 0}

    async def flaky_stream(payload: dict[str, Any]) -> Any:
        calls["attempt"] += 1
        if calls["attempt"] == 1:
            await asyncio.sleep(0.05)  # exceed chunk_timeout before first yield
            yield "never"
        else:
            yield "good-0"
            yield "good-1"

    client = MCPClientShim(max_retries=1, retry_backoff_s=0.0)
    client.tool_map = cast(dict[str, Any], {"stream": flaky_stream})

    chunks: list[str] = []
    async for chunk in client.call_tool_stream("stream", {}, chunk_timeout=0.01):
        chunks.append(chunk)

    assert chunks == ["good-0", "good-1"]
    assert calls["attempt"] == 2
