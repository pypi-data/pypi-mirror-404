import os
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from orchestrator._internal.security.ratelimit import (  # noqa: E402
    configure_rate_limit,
)
from orchestrator.adapters.fastapi_wrapper import FastAPIAdapter  # noqa: E402
from orchestrator.shared.models import ToolDefinition


# Mock Registry for execution
@pytest.fixture
def mock_registry() -> Generator[Any, None, None]:
    with patch("orchestrator.plugins.registry.get_registry") as mock_get:
        registry = MagicMock()
        plugin = MagicMock()
        plugin.get_tools.return_value = [{"name": "admin_tool"}, {"name": "user_tool"}]
        # Helper to make it awaitable
        plugin.execute = AsyncMock(return_value="success")

        registry.list.return_value = ["mock_plugin"]
        registry.get.return_value = plugin
        mock_get.return_value = registry
        yield registry

@pytest.fixture
def security_app(mock_registry: Any) -> Any:
    # reset rate limiter
    configure_rate_limit(100) # high limit for functional tests

    tools = [
        ToolDefinition(
            name="admin_tool",
            type="tool",
            description="Admin only",
            required_role="admin"
        ),
        ToolDefinition(
            name="user_tool",
            type="tool",
            description="User allowed",
            required_role="user"
        ),
         ToolDefinition(
            name="public_tool",
            type="tool",
            description="Public",
        )
    ]

    adapter = FastAPIAdapter(tools)
    return adapter.create_app(enable_security=True)

@pytest.fixture
def client(security_app: Any) -> Any:
    return TestClient(security_app)

def test_auth_missing_key(client: Any) -> None:
    # Ensure env is set to require keys
    with patch.dict(os.environ, {"TOOLWEAVER_API_KEY": "secret"}):
        response = client.get("/api/v1/tools")
        assert response.status_code == 403
        assert "not validate" in response.json()["detail"]

def test_auth_valid_key(client: Any) -> None:
    with patch.dict(os.environ, {"TOOLWEAVER_API_KEY": "secret"}):
        response = client.get(
            "/api/v1/tools",
            headers={"X-API-Key": "secret"}
        )
        assert response.status_code == 200

def test_rbac_admin_access(client: Any) -> None:
    # Admin key (convention: starts with admin-)
    with patch.dict(os.environ, {"TOOLWEAVER_API_KEY": "admin-key"}):
        # Admin tool
        response = client.post(
            "/api/v1/tools/admin_tool/execute",
            json={},
            headers={"X-API-Key": "admin-key"}
        )
        assert response.status_code == 200, response.json()
        assert response.json()["success"] is True

def test_rbac_user_denied_admin(client: Any) -> None:
    # User key
    with patch.dict(os.environ, {"TOOLWEAVER_API_KEY": "user-key"}):
        # Admin tool
        response = client.post(
            "/api/v1/tools/admin_tool/execute",
            json={},
            headers={"X-API-Key": "user-key"}
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

        # User tool - OK
        response = client.post(
            "/api/v1/tools/user_tool/execute",
            json={},
            headers={"X-API-Key": "user-key"}
        )
        assert response.status_code == 200, response.json()

def test_rate_limit(security_app: Any) -> None:
    configure_rate_limit(2) # 2 per minute
    # Re-create client to ensure it hits appropriate app
    client = TestClient(security_app)

    with patch.dict(os.environ, {"TOOLWEAVER_API_KEY": "secret"}):
        headers = {"X-API-Key": "secret"}

        # 1. OK
        assert client.get("/api/v1/tools", headers=headers).status_code == 200
        # 2. OK
        assert client.get("/api/v1/tools", headers=headers).status_code == 200
        # 3. Fail
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 429
        assert "Rate limit" in response.json()["detail"]

def test_dev_mode_bypass(client: Any) -> None:
    # If TOOLWEAVER_AUTH_DISABLED=true, allow access without key
    with patch.dict(os.environ, {"TOOLWEAVER_AUTH_DISABLED": "true"}):
        response = client.get("/api/v1/tools") # No header
        assert response.status_code == 200
