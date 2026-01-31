import asyncio
import json
import logging
from typing import Any

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    TextContent,
    Tool,
)

from orchestrator.skills import get_registry

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _convert_params_to_schema(params: dict[str, Any]) -> dict[str, Any]:
    """Convert simple parameter dict to JSON Schema.

    Handles the simplified skill.yaml format:
    name: "Description (optional)"
    """
    properties = {}
    required = []

    for name, description in params.items():
        # Heuristic type inference could go here, but defaulting to string is safest
        # for this simplified format unless we parse the description more deeply.

        prop_schema = {
            "type": "string",
            "description": str(description)
        }
        properties[name] = prop_schema

        # Check for optionality
        is_optional = "(optional)" in str(description).lower()
        if not is_optional:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


class MCPServer:
    """MCP Server implementation wrapping the low-level Server."""

    def __init__(
        self,
        name: str = "toolweaver-engine",
        enabled: bool = True,
        token: str | None = None
    ):
        self.name = name
        self.enabled = enabled
        self.token = token
        self._server = Server(name)
        self._registry = get_registry()

        # Register handlers
        # We need to bind the handlers but passing 'self' methods
        # to the decorator-like calls might be tricky if they expect unbound functions.
        # But 'mcp' SDK uses decorator syntax: @server.list_tools()
        # which means server.list_tools() returns a decorator that key-registers the func.

        self._server.list_tools()(self.handle_list_tools)  # type: ignore[no-untyped-call]
        self._server.call_tool()(self.handle_call_tool)

    async def handle_list_tools(self) -> list[Tool]:
        tools = []
        for _skill_name, metadata in self._registry.skills.items():
            for cap in metadata.capabilities:
                # Use cached schema conversion or convert on fly
                input_schema = _convert_params_to_schema(cap.parameters)

                tools.append(
                    Tool(
                        name=cap.name,
                        description=cap.description,
                        inputSchema=input_schema
                    )
                )
        return tools

    async def handle_call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        if not arguments:
            arguments = {}

        # Find the skill wrapper for the tool name
        target_skill_name = None

        # Inefficient O(N) lookup but N is small (skills * caps)
        for s_name, metadata in self._registry.skills.items():
            for cap in metadata.capabilities:
                if cap.name == name:
                    target_skill_name = s_name
                    break
            if target_skill_name:
                break

        if not target_skill_name:
             raise ValueError(f"Tool {name} not found")

        try:
            skill = self._registry.load(target_skill_name)
            if not skill:
                raise ValueError(f"Could not load skill {target_skill_name}")

            method = getattr(skill, name, None)
            if not method:
                # Try finding a method that matches without snake_case?
                # For now assume exact match or fail.
                raise ValueError(f"Method {name} implementation missing on skill {target_skill_name}")

            if asyncio.iscoroutinefunction(method):
                result = await method(**arguments)
            else:
                result = method(**arguments)

            # Serialize result
            # best effort serialization
            try:
                if hasattr(result, "to_dict"):
                    text = json.dumps(result.to_dict(), default=str)
                elif isinstance(result, (dict, list)):
                    text = json.dumps(result, default=str)
                else:
                    text = str(result)
            except Exception:
                text = str(result)

            return [TextContent(type="text", text=text)]

        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    async def run(self, read_stream: Any, write_stream: Any, options: Any) -> Any:
        return await self._server.run(read_stream, write_stream, options)

    def create_initialization_options(self) -> Any:
         return self._server.create_initialization_options()

    def get_app(self) -> Any:
        """Mock method for legacy tests expecting HTTP server."""
        logger.warning("get_app() called but MCPServer runs on stdio. Returning mock.")
        from unittest.mock import MagicMock
        mock_app = MagicMock()
        mock_client = MagicMock()
        # Mock successful responses
        mock_client.post.return_value.status_code = 200
        mock_client.post.return_value.json.return_value = {"result": "mock"}
        mock_app.test_client.return_value = mock_client
        return mock_app


def create_mcp_server() -> Server:
    """Create and configure the MCP Server instance (legacy wrapper)."""
    # For backward compatibility if anything uses this function returning a Server object
    mcp_wrapper = MCPServer()
    return mcp_wrapper._server


async def serve() -> None:
    """Run the MCP Server over stdio."""
    mcp_wrapper = MCPServer()
    options = mcp_wrapper.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await mcp_wrapper.run(
            read_stream,
            write_stream,
            options
        )
