import asyncio
from pathlib import Path
from typing import Any

import pytest
from aiohttp import web
from pytest import MonkeyPatch

from orchestrator._internal.infra.a2a_client import (
    A2AClient,
    AgentCapability,
    AgentDelegationRequest,
)


@pytest.mark.asyncio
async def test_discover_agents_loads_config() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(config_path=str(fixtures)) as client:
        agents = await client.discover_agents()
        assert len(agents) == 3
        agent_ids = {agent.agent_id for agent in agents}
        assert {"test_agent", "slow_agent", "alt_agent"} <= agent_ids


@pytest.mark.asyncio
async def test_discover_agents_filter_by_capability() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(config_path=str(fixtures)) as client:
        agents = await client.discover_agents(capability="code_generation")
        assert len(agents) == 1
        assert agents[0].agent_id == "alt_agent"


@pytest.mark.asyncio
async def test_discover_agents_filter_by_tags() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(config_path=str(fixtures)) as client:
        agents = await client.discover_agents(tags=["fast"])
        assert len(agents) == 1
        assert agents[0].agent_id == "test_agent"


@pytest.mark.asyncio
async def test_delegate_success_and_idempotency(monkeypatch: MonkeyPatch) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(config_path=str(fixtures)) as client:
        calls: list[str | None] = []

        async def _fake_delegate_http(agent: AgentCapability, request: AgentDelegationRequest) -> dict[str, Any]:
            calls.append(request.idempotency_key)
            return {"ok": True, "task": request.task}

        monkeypatch.setattr(client, "_delegate_http", _fake_delegate_http)

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="run something",
            idempotency_key="key-1",
            timeout=5,
        )

        first = await client.delegate_to_agent(request)
        second = await client.delegate_to_agent(request)

        assert first.success is True
        assert first.result == {"ok": True, "task": "run something"}
        assert second.result == first.result
        # Only first invocation should call the transport
        assert calls == ["key-1"]


@pytest.mark.asyncio
async def test_delegate_agent_not_found() -> None:
    async with A2AClient(config_path=None) as client:
        request = AgentDelegationRequest(agent_id="missing", task="noop")
        with pytest.raises(ValueError):
            await client.delegate_to_agent(request)


@pytest.mark.asyncio
async def test_delegate_timeout(monkeypatch: MonkeyPatch) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(config_path=str(fixtures)) as client:

        async def _slow_delegate_http(agent: AgentCapability, request: AgentDelegationRequest) -> dict[str, bool]:
            await asyncio.sleep(0.2)
            return {"ok": True}

        monkeypatch.setattr(client, "_delegate_http", _slow_delegate_http)

        request = AgentDelegationRequest(
            agent_id="slow_agent",
            task="slow task",
            timeout=int(0.05),
        )

        with pytest.raises(RuntimeError, match="timed out"):
            await client.delegate_to_agent(request)


@pytest.mark.asyncio
async def test_delegate_http_success() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"

    async def handle(request: web.Request) -> web.Response:
        data = await request.json()
        # Verify JSON-RPC 2.0 Request
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "execute_task"
        task = data["params"]["task"]
        rpc_id = data["id"]

        # Return JSON-RPC 2.0 Response
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"echo": task},
            "id": rpc_id
        })

    app = web.Application()
    app.router.add_post("/agents/test", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=str(fixtures)) as client:
        agent = client.get_agent("test_agent")
        assert agent is not None
        agent.endpoint = f"http://127.0.0.1:{port}/agents/test"

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="ping",
            context={},
            timeout=2,
        )

        response = await client.delegate_to_agent(request)

        assert response.success is True
        assert response.result == {"echo": "ping"}

    await runner.cleanup()


@pytest.mark.asyncio
async def test_delegate_http_legacy_fallback() -> None:
    """Test that client REJECTS simple JSON responses from non-compliant agents."""
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"

    async def handle(request: web.Request) -> web.Response:
        data = await request.json()
        task = data["params"]["task"]
        # Return Legacy Response (Plain JSON) - should fail now
        return web.json_response({"echo": task})

    app = web.Application()
    app.router.add_post("/agents/test", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=str(fixtures)) as client:
        agent = client.get_agent("test_agent")
        assert agent is not None
        agent.endpoint = f"http://127.0.0.1:{port}/agents/test"

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="ping",
            context={},
            timeout=2,
        )

        response = await client.delegate_to_agent(request)
        # Client catches the ValueError and returns success=False
        assert response.success is False
        assert response.metadata["error_type"] == "schema_error"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_delegate_http_sends_auth_header(monkeypatch: MonkeyPatch) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"

    async def handle(request: web.Request) -> web.Response:
        # Return JSON-RPC 2.0 Response
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"auth": request.headers.get("Authorization")},
            "id": "1"
        })

    app = web.Application()
    app.router.add_post("/agents/test", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    monkeypatch.setenv("TEST_TOKEN", "secret")

    async with A2AClient(config_path=str(fixtures)) as client:
        agent = client.get_agent("test_agent")
        assert agent is not None
        agent.endpoint = f"http://127.0.0.1:{port}/agents/test"
        agent.metadata["auth"] = {"type": "bearer", "token_env": "TEST_TOKEN"}

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="ping",
            context={},
            timeout=2,
        )

        response = await client.delegate_to_agent(request)
        assert response.success is True
        assert response.result["auth"] == "Bearer secret"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_delegate_retry_then_success() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    calls = {"count": 0}

    async def handle(request: web.Request) -> web.Response:
        calls["count"] += 1
        if calls["count"] < 2:
            raise web.HTTPInternalServerError()
        # Return JSON-RPC 2.0 Response
        return web.json_response({
            "jsonrpc": "2.0",
            "result": {"ok": True, "attempt": calls["count"]},
            "id": "1"
        })

    app = web.Application()
    app.router.add_post("/agents/test", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=str(fixtures), max_retries=2, retry_backoff_s=0.01) as client:
        agent = client.get_agent("test_agent")
        assert agent is not None
        agent.endpoint = f"http://127.0.0.1:{port}/agents/test"

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="ping",
            context={},
            timeout=2,
        )

        response = await client.delegate_to_agent(request)
        assert response.success is True
        assert response.result == {"ok": True, "attempt": 2}

    await runner.cleanup()


@pytest.mark.asyncio
async def test_delegate_http_server_error_returns_error_type() -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"

    async def handle(request: web.Request) -> web.Response:
        raise web.HTTPInternalServerError()

    app = web.Application()
    app.router.add_post("/agents/test", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=str(fixtures), max_retries=0) as client:
        agent = client.get_agent("test_agent")
        assert agent is not None
        agent.endpoint = f"http://127.0.0.1:{port}/agents/test"

        request = AgentDelegationRequest(
            agent_id="test_agent",
            task="ping",
            context={},
            timeout=2,
        )

        response = await client.delegate_to_agent(request)
        assert response.success is False
        assert response.metadata.get("error_type") == "server_error"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_load_config_validation(tmp_path: Path) -> None:
    bad_cfg = tmp_path / "bad_agents.yaml"
    bad_cfg.write_text("agents:\n  - name: missing id\n    endpoint: http://example.com\n")

    client = A2AClient(config_path=str(bad_cfg))
    with pytest.raises(ValueError, match="missing required"):
        await client.load()


@pytest.mark.asyncio
async def test_streaming_emits_chunks_and_events(monkeypatch: MonkeyPatch) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    events = []

    def observer(evt: str, data: dict[str, Any]) -> None:
        events.append((evt, data))

    async def fake_stream(agent: AgentCapability, request: AgentDelegationRequest, chunk_timeout: float | None) -> Any:
        for i in range(2):
            await asyncio.sleep(0)
            yield f"chunk-{i}"

    async with A2AClient(config_path=str(fixtures), observer=observer) as client:
        monkeypatch.setattr(client, "_delegate_stream", fake_stream)
        request = AgentDelegationRequest(agent_id="test_agent", task="stream")

        chunks = []
        async for chunk in client.delegate_stream(request, chunk_timeout=1):
            chunks.append(chunk)

    assert chunks == ["chunk-0", "chunk-1"]
    assert any(e[0] == "a2a.stream.start" for e in events)
    assert any(e[0] == "a2a.stream.chunk" for e in events)
    assert any(e[0] == "a2a.stream.complete" and e[1].get("success") is True for e in events)


@pytest.mark.asyncio
async def test_streaming_retries_on_chunk_timeout(monkeypatch: MonkeyPatch) -> None:
    events = []

    def observer(evt: str, data: dict[str, Any]) -> None:
        events.append((evt, data))

    attempt = {"count": 0}

    async def flaky_stream(agent: AgentCapability, request: AgentDelegationRequest, chunk_timeout: float | None) -> Any:
        attempt["count"] += 1
        if attempt["count"] == 1:
            raise asyncio.TimeoutError()
        else:
            yield "ok-0"
            yield "ok-1"

    fixtures = Path(__file__).parent / "fixtures" / "agents.yaml"
    async with A2AClient(
        config_path=str(fixtures), observer=observer, max_retries=1, retry_backoff_s=0.0
    ) as client:
        monkeypatch.setattr(client, "_delegate_stream", flaky_stream)
        request = AgentDelegationRequest(agent_id="test_agent", task="stream")

        chunks = []
        async for chunk in client.delegate_stream(request, chunk_timeout=0.01):
            chunks.append(chunk)

    assert chunks == ["ok-0", "ok-1"]
    assert attempt["count"] == 2
    assert any(e[0] == "a2a.stream.start" for e in events)


@pytest.mark.asyncio
async def test_streaming_sse() -> None:
    async def sse_handler(request: web.Request) -> web.StreamResponse:
        resp = web.StreamResponse(
            status=200, reason="OK", headers={"Content-Type": "text/event-stream"}
        )
        await resp.prepare(request)
        await resp.write(b"data: chunk-0\n\n")
        await resp.write(b"data: chunk-1\n\n")
        await resp.write_eof()
        return resp

    app = web.Application()
    app.router.add_get("/sse", sse_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=None) as client:
        client.register_agent(
            AgentCapability(
                agent_id="sse_agent",
                name="sse",
                description="sse",
                endpoint=f"http://127.0.0.1:{port}/sse",
                protocol="sse",
            )
        )
        request = AgentDelegationRequest(agent_id="sse_agent", task="t")
        chunks = []
        async for c in client.delegate_stream(request, chunk_timeout=1):
            chunks.append(c)

    await runner.cleanup()

    assert chunks == ["chunk-0", "chunk-1"]


@pytest.mark.asyncio
async def test_streaming_websocket() -> None:
    async def ws_handler(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_str("chunk-0")
        await ws.send_str("chunk-1")
        await ws.close()
        return ws

    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    async with A2AClient(config_path=None) as client:
        client.register_agent(
            AgentCapability(
                agent_id="ws_agent",
                name="ws",
                description="ws",
                endpoint=f"http://127.0.0.1:{port}/ws",
                protocol="websocket",
            )
        )
        request = AgentDelegationRequest(agent_id="ws_agent", task="t")
        chunks = []
        async for c in client.delegate_stream(request, chunk_timeout=1):
            chunks.append(c)

    await runner.cleanup()

    assert chunks == ["chunk-0", "chunk-1"]


@pytest.mark.asyncio
async def test_config_env_expansion(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    cfg = tmp_path / "agents_env.yaml"
    monkeypatch.setenv("BASE_URL", "http://example.com")
    cfg.write_text(
        """
agents:
  - agent_id: env_agent
    name: Env Agent
    endpoint: ${BASE_URL}/agents/handler
    capabilities: ["test"]
        """
    )

    async with A2AClient(config_path=str(cfg)) as client:
        agent = client.get_agent("env_agent")
        assert agent is not None
        assert agent.endpoint == "http://example.com/agents/handler"
