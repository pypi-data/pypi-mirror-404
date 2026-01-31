import asyncio
from collections.abc import AsyncIterator
from typing import Any, cast

import pytest

from orchestrator._internal.dispatch.hybrid_dispatcher import dispatch_step
from orchestrator._internal.infra.a2a_client import A2AClient, AgentDelegationRequest
from orchestrator._internal.infra.mcp_client import MCPClientShim


class DummyMCP:
    def __init__(self) -> None:
        self.tool_map: dict[str, Any] = {}


class DummyResponse:
    def __init__(self, result: Any) -> None:
        self.result = result


class DummyA2A(A2AClient):
    def __init__(self, responses: dict[str, Any] | None = None, stream_chunks: dict[str, list[str]] | None = None) -> None:
        super().__init__(config_path=None)
        self.responses = responses or {}
        self.stream_chunks = stream_chunks or {}
        self.calls: list[tuple[str, str]] = []

    async def delegate_to_agent(self, request: AgentDelegationRequest) -> Any:
        self.calls.append(("delegate", request.agent_id))
        payload = self.responses.get(request.agent_id, None)
        # Return shape matching AgentDelegationResponse
        return {
            "agent_id": request.agent_id,
            "success": True,
            "result": payload,
            "execution_time": 0.01,
            "cost": None,
            "metadata": {},
        }

    async def delegate_stream(
        self, request: AgentDelegationRequest, chunk_timeout: float | None = None
    ) -> AsyncIterator[str]:
        self.calls.append(("stream", request.agent_id))
        for chunk in self.stream_chunks.get(request.agent_id, []):
            await asyncio.sleep(0)
            yield chunk


@pytest.mark.asyncio
async def test_dispatch_agent_delegation_returns_result() -> None:
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A(responses={"agent_1": {"ok": True}})

    step = {
        "tool": "agent_agent_1",
        "input": {"task": "do", "context": {"x": 1}},
        "timeout_s": 5,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"ok": True}
    assert ("delegate", "agent_1") in a2a.calls


@pytest.mark.asyncio
async def test_dispatch_agent_streaming_collects_chunks() -> None:
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A(stream_chunks={"agent_stream": ["c1", "c2"]})

    step = {
        "tool": "agent_agent_stream",
        "input": {"task": "stream"},
        "stream": True,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"chunks": ["c1", "c2"]}
    assert ("stream", "agent_stream") in a2a.calls


@pytest.mark.asyncio
async def test_dispatch_mcp_streaming_collects_chunks() -> None:
    async def worker(payload: dict[str, Any]) -> AsyncIterator[str]:
        yield "m1"
        yield "m2"

    class MCP:
        def __init__(self) -> None:
            self.tool_map: dict[str, Any] = {"stream_tool": worker}

        async def call_tool_stream(
            self, name: str, payload: dict[str, Any], timeout: float = 30, chunk_timeout: float | None = None
        ) -> AsyncIterator[str]:
            async for c in worker(payload):
                yield c

        async def call_tool(
            self, name: str, payload: dict[str, Any], idempotency_key: str | None = None, timeout: float = 30
        ) -> str:
            return "not-used"

    mcp = cast(MCPClientShim, MCP())
    a2a = DummyA2A()

    step = {
        "tool": "stream_tool",
        "input": {},
        "stream": True,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"chunks": ["m1", "m2"]}
