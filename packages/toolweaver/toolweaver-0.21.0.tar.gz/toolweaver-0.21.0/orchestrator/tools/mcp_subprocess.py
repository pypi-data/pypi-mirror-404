"""
Generic MCP Subprocess Client

Launches any MCP server (Node.js, Python, Go, Rust) as a subprocess
and communicates via JSON-RPC over stdio (MCP standard protocol).

This enables seamless integration with services like:
- Microsoft Work IQ MCP (@microsoft/workiq)
- Any other MCP-compliant server

Design:
- Wraps Anthropic's mcp.client.subprocess for protocol handling
- Provides ToolWeaver-specific integration patterns
- Configurable via .env for flexibility

Example:
    config = MCPServerConfig(
        name="work_iq",
        command=["npx", "-y", "@microsoft/workiq", "mcp"],
        env_vars={"WORK_IQ_TENANT_ID": "your-tenant-id"}
    )

    client = MCPSubprocessClient(config)
    await client.start()

    tools = await client.list_tools()
    result = await client.call_tool("email_search", {"query": "important"})

    await client.stop()
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for MCP subprocess server."""

    name: str
    """Adapter name (e.g., 'work_iq', 'some_other_mcp')"""

    command: list[str]
    """Full command as list: ['npx', '-y', '@microsoft/workiq', 'mcp']"""

    env_vars: dict[str, str] | None = None
    """Optional environment variables to pass to subprocess"""

    timeout_s: int = 30
    """Timeout for MCP communication"""

    enable_auto_register: bool = True
    """Auto-register discovered tools with ToolWeaver catalog on startup"""

    @staticmethod
    def create_from_env(
        config_prefix: str,
        default_timeout_s: int = 30,
    ) -> "MCPServerConfig":
        """
        Create MCPServerConfig from environment variables.

        Looks for:
        - {PREFIX}_COMMAND: Command as comma-separated string
        - {PREFIX}_*: Additional env vars to pass to subprocess

        Example:
            # In .env:
            WORK_IQ_COMMAND=npx,-y,@microsoft/workiq,mcp
            WORK_IQ_TENANT_ID=your-tenant-id

            # In code:
            config = MCPServerConfig.create_from_env("WORK_IQ")

        Args:
            config_prefix: Prefix for env var lookup (e.g., "WORK_IQ")
            default_timeout_s: Default timeout if not specified

        Returns:
            MCPServerConfig instance

        Raises:
            ValueError: If required vars not found
        """
        command_str = os.getenv(f"{config_prefix}_COMMAND")
        if not command_str:
            raise ValueError(f"{config_prefix}_COMMAND not found in environment")

        command = command_str.split(",")

        # Collect additional env vars
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(config_prefix) and key != f"{config_prefix}_COMMAND":
                # Use the suffix as the env var name
                suffix = key[len(config_prefix) + 1 :]
                env_vars[suffix] = value

        return MCPServerConfig(
            name=config_prefix.lower(),
            command=command,
            env_vars=env_vars if env_vars else None,
            timeout_s=default_timeout_s,
        )


class MCPSubprocessClient:
    """
    Generic MCP client for subprocess-based MCP servers.

    Handles:
    - Subprocess lifecycle (spawn, cleanup)
    - JSON-RPC protocol (via Anthropic's mcp library)
    - Tool discovery
    - Tool execution
    - Integration with ToolWeaver tool registry

    This is a lightweight wrapper that defers to the mcp library for
    all protocol handling. We focus on ToolWeaver-specific patterns.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.mcp_client: Any = None
        self.tools_cache: dict[str, Any] | None = None
        self._stdio_context: Any = None  # Reference to stdio_client context

    async def start(self) -> None:
        """
        Start the MCP subprocess and initialize connection.

        Raises:
            RuntimeError: If subprocess fails to start or initialization fails
        """
        logger.info(f"[MCP] Starting subprocess: {self.config.name}")
        logger.debug(f"[MCP] Command: {' '.join(self.config.command)}")

        # Import here to avoid hard dependency if mcp not installed
        try:
            from mcp.client.session import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as e:
            raise RuntimeError(
                "mcp library not found. Install with: pip install mcp"
            ) from e

        # Merge environment variables
        env = os.environ.copy()
        if self.config.env_vars:
            env.update(self.config.env_vars)
            logger.debug(f"[MCP] Env vars: {list(self.config.env_vars.keys())}")

        try:
            # Create stdio server parameters
            # The first element is the command, rest are args
            cmd = self.config.command[0] if self.config.command else "npx"
            args = self.config.command[1:] if len(self.config.command) > 1 else []

            server_params = StdioServerParameters(
                command=cmd,
                args=args,
                env=env if self.config.env_vars else None,
            )

            # Start the subprocess via stdio_client (async context manager)
            self._stdio_context = stdio_client(server_params)
            transport = await self._stdio_context.__aenter__()

            # Create and initialize session with transport streams
            # transport is a tuple of (read_stream, write_stream) from the context manager
            self.mcp_client = ClientSession(
                read_stream=transport[0],
                write_stream=transport[1],
            )
            await self.mcp_client.__aenter__()

            logger.info(f"[MCP] ✓ {self.config.name} ready")

        except Exception as e:
            logger.error(f"[MCP] ✗ Failed to start {self.config.name}: {e}")
            await self.stop()
            raise RuntimeError(
                f"Failed to start MCP subprocess '{self.config.name}': {e}"
            ) from e

    async def stop(self) -> None:
        """Gracefully stop the MCP subprocess."""
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"[MCP] Error closing session: {e}")
            finally:
                self.mcp_client = None

        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"[MCP] Error closing stdio context: {e}")
            finally:
                self._stdio_context = None

        # Clear tools cache
        self.tools_cache = None

        logger.debug(f"[MCP] {self.config.name} stopped")

    async def list_tools(self) -> list[Any]:
        """
        Discover available tools from MCP server.

        Returns:
            List of Tool objects with name, description, schema
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call start() first.")

        if self.tools_cache is not None:
            return list(self.tools_cache.values())

        logger.debug(f"[MCP] Discovering tools from {self.config.name}...")

        try:
            response = await self.mcp_client.list_tools()
            tools = response.tools
            self.tools_cache = {tool.name: tool for tool in tools}

            sample_names = [t.name for t in tools[:5]]
            names_str = ", ".join(sample_names)
            if len(tools) > 5:
                names_str += "..."

            logger.info(f"[MCP] Found {len(tools)} tools from {self.config.name}: {names_str}")

            return cast(list[Any], tools)

        except Exception as e:
            logger.error(f"[MCP] Failed to list tools: {e}")
            raise

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Execute a tool from the MCP server.

        Args:
            tool_name: Name of the tool (e.g., 'email_search')
            arguments: Tool arguments as dict

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool execution fails
        """
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call start() first.")

        logger.debug(
            f"[MCP] Calling {self.config.name}:{tool_name} with args: {arguments}"
        )

        try:
            result = await self.mcp_client.call_tool(
                name=tool_name,
                arguments=arguments,
            )

            logger.debug(f"[MCP] Tool result: {result}")
            return result

        except Exception as e:
            logger.error(
                f"[MCP] Tool call failed: {self.config.name}:{tool_name} → {e}"
            )
            raise RuntimeError(f"Failed to call tool '{tool_name}': {e}") from e

    async def register_with_catalog(self) -> None:
        """
        Auto-register discovered tools with ToolWeaver's tool catalog.

        This converts MCP tools to ToolWeaver format and registers them
        so they can be used in orchestration plans.
        """
        if not self.config.enable_auto_register:
            logger.debug(f"[MCP] Auto-registration disabled for {self.config.name}")
            return

        tools = await self.list_tools()

        # Import here to avoid circular dependency
        try:
            from orchestrator.tools.discovery_api import (  # type: ignore[attr-defined]
                get_tool_registry,
            )
        except ImportError:
            logger.warning("[MCP] Tool registry not available, skipping registration")
            return

        registry = get_tool_registry()

        for tool in tools:
            tool_id = f"{self.config.name}:{tool.name}"

            logger.debug(f"[MCP] Registering tool: {tool_id}")

            # Create wrapper function that calls MCP tool
            async def tool_wrapper(
                tool_name: str = tool.name,
                mcp_client_ref: Any = self,
                **kwargs: Any,
            ) -> Any:
                """Wrapper for MCP tool execution."""
                return await mcp_client_ref.call_tool(tool_name, kwargs)

            # Register in catalog
            try:
                registry.register_tool(
                    name=tool_id,
                    tool=tool_wrapper,
                    metadata={"description": tool.description or tool.name},
                )
                logger.info(f"[MCP] ✓ Registered {tool_id}")
            except Exception as e:
                logger.warning(f"[MCP] Failed to register {tool_id}: {e}")


# Context manager support for cleaner usage
class MCPSubprocessContext:
    """Context manager for MCPSubprocessClient lifecycle."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.client: MCPSubprocessClient | None = None

    async def __aenter__(self) -> MCPSubprocessClient:
        """Start the MCP client on context entry."""
        self.client = MCPSubprocessClient(self.config)
        await self.client.start()
        return self.client

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the MCP client on context exit."""
        if self.client:
            await self.client.stop()
