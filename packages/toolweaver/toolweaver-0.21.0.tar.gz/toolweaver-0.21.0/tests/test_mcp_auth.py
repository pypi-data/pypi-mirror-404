import base64

import pytest

pytest.importorskip("aiohttp")

from orchestrator._internal.infra.mcp_auth import MCPAuthConfig, MCPAuthManager
from orchestrator.tools.mcp_adapter import MCPHttpAdapterPlugin


def test_mcp_auth_headers_none() -> None:
    headers = MCPAuthManager().get_headers(MCPAuthConfig(type="none"))
    assert headers == {}


def test_mcp_auth_headers_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "abc123")
    config = MCPAuthConfig(type="bearer", token_env="MCP_TOKEN")
    headers = MCPAuthManager().get_headers(config)
    assert headers == {"Authorization": "Bearer abc123"}


def test_mcp_auth_headers_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_API_KEY", "key-xyz")
    config = MCPAuthConfig(type="api_key", token_env="MCP_API_KEY", header_name="X-Api-Key")
    headers = MCPAuthManager().get_headers(config)
    assert headers == {"X-Api-Key": "key-xyz"}


def test_mcp_auth_headers_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_USER", "user1")
    monkeypatch.setenv("MCP_PASS", "pass1")
    config = MCPAuthConfig(
        type="basic",
        username_env="MCP_USER",
        password_env="MCP_PASS",
    )
    headers = MCPAuthManager().get_headers(config)
    expected = base64.b64encode(b"user1:pass1").decode()
    assert headers == {"Authorization": f"Basic {expected}"}


def test_mcp_adapter_merges_auth_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "abc123")
    config = MCPAuthConfig(type="bearer", token_env="MCP_TOKEN")
    adapter = MCPHttpAdapterPlugin(
        "http://example.com",
        headers={"X-Static": "1"},
        auth=config,
    )
    assert adapter.headers["Authorization"] == "Bearer abc123"
    assert adapter.headers["X-Static"] == "1"
