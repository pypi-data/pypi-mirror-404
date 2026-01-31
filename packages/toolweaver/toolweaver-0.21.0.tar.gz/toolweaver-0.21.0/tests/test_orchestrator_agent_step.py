
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
        self.tool_map: dict[str, Any] = {}


def _make_response(request: AgentDelegationRequest, result: dict[str, Any], success: bool = True) -> AgentDelegationResponse:
    return AgentDelegationResponse(
        agent_id=request.agent_id,
        success=success,
        result=result,
        execution_time=0.0,
        metadata={},
        cost=None,
    )


class DummyA2A(A2AClient):
    def __init__(self) -> None:
        super().__init__(config_path=None)
        self.calls: list[Any] = []

    async def delegate_to_agent(self, request: AgentDelegationRequest) -> AgentDelegationResponse:
        self.calls.append(request)
        return _make_response(request, {"ok": True, "context": request.context, "task": request.task})

    async def delegate_stream(
        self, request: AgentDelegationRequest, chunk_timeout: float | None = None
    ) -> AsyncIterator[str]:
        self.calls.append(("stream", request.agent_id, chunk_timeout))
        yield "c1"
        yield "c2"


@pytest.mark.asyncio
async def test_run_step_agent_type_builds_context_and_delegates() -> None:
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A()

    step = {
        "type": "agent",
        "agent_id": "agent_1",
        "task": "do something",
        "inputs": ["foo"],
        "timeout_s": 5,
    }
    step_outputs = {"foo": {"bar": 1}}

    result = await run_step(step, step_outputs, mcp, monitor=None, a2a_client=a2a)

    assert result == {"ok": True, "context": {"foo": {"bar": 1}}, "task": "do something"}
    assert len(a2a.calls) == 1
    assert a2a.calls[0].agent_id == "agent_1"
    assert a2a.calls[0].context == {"foo": {"bar": 1}}


@pytest.mark.asyncio
async def test_run_step_agent_type_streams_when_requested() -> None:
    mcp = cast(MCPClientShim, DummyMCP())
    a2a = DummyA2A()

    step = {
        "type": "agent",
        "agent_id": "agent_stream",
        "task": "stream",
        "stream": True,
        "chunk_timeout_s": 0.5,
    }

    result = await run_step(step, {}, mcp, monitor=None, a2a_client=a2a)

    assert result == {"chunks": ["c1", "c2"]}
    # Second call entry is the streaming tuple
    assert ("stream", "agent_stream", 0.5) in a2a.calls
