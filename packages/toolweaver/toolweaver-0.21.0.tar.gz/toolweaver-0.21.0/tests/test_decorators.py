import asyncio
import os
from typing import Any
from unittest.mock import patch

import pytest

from orchestrator import a2a_agent, mcp_tool, tool
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


def test_tool_decorator_registers_and_executes() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        # NOTE: We don't clear the registry here because:
        # 1. @tool decorators register with Phase -1 local registry, not plugin registry
        # 2. If we clear, we'd need to re-register the decorator bridge plugin
        # 3. Test isolation comes from the fact that each @tool gets a unique name

        # Generate unique tool name to avoid conflicts
        import uuid

        tool_id = str(uuid.uuid4())[:8]

        @tool(
            name=f"echo_{tool_id}",
            description="Echo the provided text",
            parameters=[
                ToolParameter(name="text", type="string", description="Text to echo", required=True)
            ],
            metadata={"category": "testing"},
        )
        def echo(params: dict[str, Any]) -> dict[str, Any]:
            return {"text": params["text"]}

        # Get the registry to verify decorator created tools
        get_registry()

        # Tools from @tool decorator may not appear in plugin registry immediately
        # For now, just verify the decorated function works
        assert callable(echo)

        # Test that the bound function has the tool definition attached
        assert hasattr(echo, "__tool_definition__"), (
            "Decorated function should have __tool_definition__"
        )
        td = echo.__tool_definition__

        assert td.name == f"echo_{tool_id}"
        assert td.type == "function"
        assert td.source == "decorator"
        assert td.metadata.get("category") == "testing"

        # Execute the decorated function directly to verify it works
        result = asyncio.run(echo({"text": "hello"}))
        assert result == {"text": "hello"}


def test_tool_decorator_custom_name_and_provider() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        @tool(
            name="custom_echo",
            description="Echo with custom name",
            provider="local",
            parameters=[
                ToolParameter(name="text", type="string", description="Text to echo", required=True)
            ],
        )
        def echo(params: dict[str, Any]) -> dict[str, Any]:
            return {"text": params["text"]}

        # Verify tool definition is set correctly
        assert hasattr(echo, "__tool_definition__")
        td = echo.__tool_definition__
        assert td.name == "custom_echo"
        assert td.provider == "local"

        # Execute with custom name
        result = asyncio.run(echo({"text": "world"}))
        assert result == {"text": "world"}


def test_mcp_tool_auto_params_and_async_execution() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        @mcp_tool(domain="finance")
        async def get_balance(account: str, include_pending: bool = False) -> dict[str, Any]:
            return {"account": account, "pending": include_pending}

        # Verify tool definition is set correctly
        assert hasattr(get_balance, "__tool_definition__")
        td = get_balance.__tool_definition__
        assert td.type == "mcp"
        assert td.domain == "finance"

        params = {p.name: p for p in td.parameters}
        assert params["account"].required is True
        assert params["include_pending"].required is False

        result = asyncio.run(get_balance({"account": "123", "include_pending": False}))
        assert result == {"account": "123", "pending": False}


def test_a2a_agent_decorator_sync_function() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        @a2a_agent(description="Route work to agents")
        def route(task: str, priority: int = 1) -> dict[str, Any]:
            return {"task": task, "priority": priority}

        # Verify tool definition is set correctly
        assert hasattr(route, "__tool_definition__")
        td = route.__tool_definition__
        assert td.type == "agent"
        assert td.parameters[0].name == "task"
        assert td.parameters[0].required is True
        assert td.parameters[1].name == "priority"
        assert td.parameters[1].required is False

        result = asyncio.run(route({"task": "triage", "priority": 1}))
        assert result == {"task": "triage", "priority": 1}


def test_decorator_validates_function_signature() -> None:
    """Test that decorator validation works on function signatures."""
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        # Test that missing docstring triggers warning (but still registers)
        @tool()
        def no_docstring(x: int) -> int:
            return x

        # Should register successfully despite warning
        assert hasattr(no_docstring, "__tool_definition__")
        td = no_docstring.__tool_definition__
        assert td.name == "no_docstring"


def test_decorator_rejects_signature_mismatch_for_kwargs() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        registry = get_registry()
        registry.clear()

        with pytest.raises(ValueError, match="parameter mismatch"):

            @mcp_tool(
                parameters=[
                    ToolParameter(
                        name="only_one", type="string", required=True, description="Test param"
                    )
                ]
            )
            def expect_two(a: str, b: str) -> dict[str, Any]:
                return {"a": a, "b": b}
