"""
Test MCPSubprocessClient - configuration and basic validation.

Note: Full integration tests require actual MCP servers.
These tests validate the client infrastructure.
"""

from typing import Any

import pytest

from orchestrator.tools.mcp_subprocess import MCPServerConfig, MCPSubprocessClient


class TestMCPServerConfig:
    """Test MCPServerConfig creation and validation."""

    def test_direct_creation(self) -> None:
        """Test creating config with explicit parameters."""
        config = MCPServerConfig(
            name="test_mcp",
            command=["npx", "-y", "@microsoft/workiq", "mcp"],
            env_vars={"TENANT_ID": "test-tenant"},
            timeout_s=60,
        )

        assert config.name == "test_mcp"
        assert config.command == ["npx", "-y", "@microsoft/workiq", "mcp"]
        assert config.env_vars == {"TENANT_ID": "test-tenant"}
        assert config.timeout_s == 60
        assert config.enable_auto_register is True

    def test_create_from_env(self, monkeypatch: Any) -> None:
        """Test creating config from environment variables."""
        monkeypatch.setenv("TEST_MCP_COMMAND", "npx,-y,@test/mcp,mcp")
        monkeypatch.setenv("TEST_MCP_TENANT_ID", "my-tenant")
        monkeypatch.setenv("TEST_MCP_API_KEY", "secret-key")

        config = MCPServerConfig.create_from_env("TEST_MCP")

        assert config.name == "test_mcp"
        assert config.command == ["npx", "-y", "@test/mcp", "mcp"]
        assert config.env_vars == {"TENANT_ID": "my-tenant", "API_KEY": "secret-key"}

    def test_create_from_env_missing_command(self, monkeypatch: Any) -> None:
        """Test error when COMMAND env var is missing."""
        monkeypatch.delenv("MISSING_MCP_COMMAND", raising=False)

        with pytest.raises(ValueError, match="MISSING_MCP_COMMAND not found"):
            MCPServerConfig.create_from_env("MISSING_MCP")

    def test_create_from_env_with_timeout(self, monkeypatch: Any) -> None:
        """Test creating config with custom timeout."""
        monkeypatch.setenv("CUSTOM_MCP_COMMAND", "python,-m,custom_mcp")

        config = MCPServerConfig.create_from_env("CUSTOM_MCP", default_timeout_s=120)

        assert config.timeout_s == 120


class TestMCPSubprocessClient:
    """Test MCPSubprocessClient initialization and basic operations."""

    def test_client_initialization(self) -> None:
        """Test client creation with config."""
        config = MCPServerConfig(
            name="test",
            command=["echo", "test"],
        )

        client = MCPSubprocessClient(config)

        assert client.config == config
        assert client.mcp_client is None
        assert client.tools_cache is None

    @pytest.mark.asyncio
    async def test_client_stop_without_start(self) -> None:
        """Test stopping client that was never started."""
        config = MCPServerConfig(name="test", command=["echo", "test"])
        client = MCPSubprocessClient(config)

        # Should not raise
        await client.stop()

    def test_client_list_tools_before_start(self) -> None:
        """Test that list_tools raises if not started."""
        config = MCPServerConfig(name="test", command=["echo", "test"])
        client = MCPSubprocessClient(config)

        with pytest.raises(RuntimeError, match="not initialized"):
            import asyncio

            asyncio.run(client.list_tools())

    def test_client_call_tool_before_start(self) -> None:
        """Test that call_tool raises if not started."""
        config = MCPServerConfig(name="test", command=["echo", "test"])
        client = MCPSubprocessClient(config)

        with pytest.raises(RuntimeError, match="not initialized"):
            import asyncio

            asyncio.run(client.call_tool("test_tool", {}))


class TestMCPServerConfigParsing:
    """Test command parsing from environment."""

    def test_command_parsing_simple(self, monkeypatch: Any) -> None:
        """Test parsing simple command."""
        monkeypatch.setenv("SIMPLE_COMMAND", "python,-m,mcp")
        config = MCPServerConfig.create_from_env("SIMPLE")

        assert config.command == ["python", "-m", "mcp"]

    def test_command_parsing_with_flags(self, monkeypatch: Any) -> None:
        """Test parsing command with flags."""
        monkeypatch.setenv("FLAGS_COMMAND", "npx,-y,@pkg/mcp,mcp,--debug,--port,8000")
        config = MCPServerConfig.create_from_env("FLAGS")

        assert config.command == ["npx", "-y", "@pkg/mcp", "mcp", "--debug", "--port", "8000"]

    def test_env_var_collection(self, monkeypatch: Any) -> None:
        """Test that all prefix-matching env vars are collected."""
        monkeypatch.setenv("COLLECT_COMMAND", "test")
        monkeypatch.setenv("COLLECT_VAR1", "value1")
        monkeypatch.setenv("COLLECT_VAR2", "value2")
        monkeypatch.setenv("COLLECT_VAR3", "value3")
        monkeypatch.setenv("OTHER_VAR", "should_not_collect")

        config = MCPServerConfig.create_from_env("COLLECT")

        assert config.env_vars is not None
        assert len(config.env_vars) == 3
        assert config.env_vars["VAR1"] == "value1"
        assert config.env_vars["VAR2"] == "value2"
        assert config.env_vars["VAR3"] == "value3"
        assert "OTHER_VAR" not in config.env_vars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
