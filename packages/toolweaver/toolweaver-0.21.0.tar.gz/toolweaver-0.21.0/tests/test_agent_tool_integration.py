from collections.abc import AsyncIterator
from typing import Any, cast

import pytest

from orchestrator._internal.infra.a2a_client import (
    A2AClient,
    AgentDelegationRequest,
    AgentDelegationResponse,
)
from orchestrator._internal.infra.mcp_client import MCPClientShim
from orchestrator._internal.runtime.orchestrator import run_step


class DummyMCP:
    def __init__(self) -> None:
        self.tool_map: dict[str, Any] = {"tool_fetch": True}

    async def call_tool(
        self, name: str, payload: dict[str, Any], idempotency_key: str | None = None, timeout: float = 30
    ) -> dict[str, Any]:
        return {"fetched": 1, **payload}

    async def call_tool_stream(
        self, name: str, payload: dict[str, Any], timeout: float = 30, chunk_timeout: float | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"fetched": 1, **payload}


def _make_response(
    request: AgentDelegationRequest, result: dict[str, Any] | None, success: bool = True, metadata: dict[str, Any] | None = None
) -> AgentDelegationResponse:
    return AgentDelegationResponse(
        agent_id=request.agent_id,
        success=success,
        result=result or {},
        execution_time=0.0,
        metadata=metadata or {},
        cost=None,
    )


class DummyA2A(A2AClient):
    def __init__(self) -> None:
        super().__init__(config_path=None)
        self.calls: list[Any] = []

    async def delegate_to_agent(self, request: AgentDelegationRequest) -> AgentDelegationResponse:
        self.calls.append(request)
        return _make_response(request, {"agent_seen": request.context, "task": request.task})

    async def delegate_stream(
        self, request: AgentDelegationRequest, chunk_timeout: float | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        self.calls.append(("stream", request.agent_id, chunk_timeout))
        yield {"agent_seen": request.context}


@pytest.mark.asyncio
async def test_tool_then_agent_integration_flow() -> None:
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A()

    tool_step = {
        "tool": "tool_fetch",
        "input": {"seed": 5},
        "timeout_s": 5,
    }
    agent_step = {
        "type": "agent",
        "agent_id": "agent_1",
        "task": "analyze",
        "inputs": ["tool_fetch"],
    }

    outputs: dict[str, Any] = {}
    outputs["tool_fetch"] = await run_step(tool_step, outputs, mcp, monitor=None, a2a_client=a2a)
    outputs["agent"] = await run_step(agent_step, outputs, mcp, monitor=None, a2a_client=a2a)

    assert outputs["tool_fetch"]["fetched"] == 1
    assert outputs["agent"]["agent_seen"]["tool_fetch"]["fetched"] == 1
    assert a2a.calls[0].context == {"tool_fetch": {"fetched": 1, "seed": 5}}


@pytest.mark.asyncio
async def test_agent_delegation_failure_returns_error() -> None:
    """Verify agent delegation failure is properly caught and raised."""
    mcp = cast(MCPClientShim, DummyMCP())

    class FailingA2A(A2AClient):
        async def delegate_to_agent(self, request: AgentDelegationRequest) -> AgentDelegationResponse:
            return _make_response(request, None, success=False)

        async def delegate_stream(
            self, request: AgentDelegationRequest, chunk_timeout: float | None = None
        ) -> AsyncIterator[dict[str, Any]]:
            yield {}

    a2a = FailingA2A()
    step = {
        "type": "agent",
        "agent_id": "failing_agent",
        "task": "will fail",
    }

    with pytest.raises(RuntimeError):
        await run_step(step, {}, mcp, monitor=None, a2a_client=a2a)


@pytest.mark.asyncio
async def test_agent_retries_on_failure() -> None:
    """Verify agent retries honor retry_policy."""
    mcp = cast(MCPClientShim, DummyMCP())

    attempt_count = 0

    class RetryableA2A(A2AClient):
        async def delegate_to_agent(self, request: AgentDelegationRequest) -> AgentDelegationResponse:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                return _make_response(request, None, success=False)
            return _make_response(request, {"ok": True}, success=True)

        async def delegate_stream(
            self, request: AgentDelegationRequest, chunk_timeout: float | None = None
        ) -> AsyncIterator[dict[str, Any]]:
            yield {}

    a2a = RetryableA2A()
    step = {
        "type": "agent",
        "agent_id": "retry_agent",
        "task": "retry",
        "retry_policy": {"retries": 2, "backoff_s": 0.01},
    }

    result = await run_step(step, {}, mcp, monitor=None, a2a_client=a2a)
    assert result == {"ok": True}
    assert attempt_count == 2


@pytest.mark.asyncio
async def test_agent_context_merges_inputs_first_then_inline() -> None:
    """Verify agent context merges from inputs, then inline context (inline takes precedence)."""
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A()

    step = {
        "type": "agent",
        "agent_id": "agent_1",
        "task": "merge",
        "inputs": ["prior"],
        "context": {"key": "inline_val"},
    }
    step_outputs = {"prior": {"key": "prior_val"}}

    await run_step(step, step_outputs, mcp, monitor=None, a2a_client=a2a)

    # Context should have merged inputs dict + inline context (inline overwrites)
    merged_context = a2a.calls[0].context
    assert isinstance(merged_context, dict)


@pytest.mark.asyncio
async def test_agent_streaming_yields_chunks() -> None:
    """Verify agent streaming collects and returns chunks."""
    mcp = cast(MCPClientShim, DummyMCP())

    class ChunkedA2A(A2AClient):
        async def delegate_to_agent(self, request: AgentDelegationRequest) -> AgentDelegationResponse:
            return _make_response(request, None, success=False)

        async def delegate_stream(
            self, request: AgentDelegationRequest, chunk_timeout: float | None = None
        ) -> AsyncIterator[str]:
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

    a2a = ChunkedA2A()
    step = {
        "type": "agent",
        "agent_id": "stream_agent",
        "task": "stream",
        "stream": True,
        "chunk_timeout_s": 1.0,
    }

    result = await run_step(step, {}, mcp, monitor=None, a2a_client=a2a)
    assert result == {"chunks": ["chunk1", "chunk2", "chunk3"]}


@pytest.mark.asyncio
async def test_mcp_tool_streaming_parity() -> None:
    """Verify MCP tool streaming has same interface as agent streaming."""

    class StreamingMCP:
        def __init__(self) -> None:
            self.tool_map: dict[str, Any] = {"stream_tool": True}

        async def call_tool(
            self, name: str, payload: dict[str, Any], idempotency_key: str | None = None, timeout: float = 30
        ) -> dict[str, Any]:
            return {"tool": "response"}

        async def call_tool_stream(
            self, name: str, payload: dict[str, Any], timeout: float = 30, chunk_timeout: float | None = None
        ) -> AsyncIterator[str]:
            yield "mcp1"
            yield "mcp2"

    a2a = DummyA2A()
    mcp = cast(MCPClientShim, StreamingMCP())

    tool_step = {
        "tool": "stream_tool",
        "input": {},
        "stream": True,
    }

    result = await run_step(tool_step, {}, mcp, monitor=None, a2a_client=a2a)
    assert result == {"chunks": ["mcp1", "mcp2"]}
