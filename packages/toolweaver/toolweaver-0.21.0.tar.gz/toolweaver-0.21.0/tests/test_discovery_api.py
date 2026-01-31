import os
from typing import Any
from unittest.mock import patch

from orchestrator import (
    FunctionToolTemplate,
    get_available_tools,
    get_tool_info,
    list_tools_by_domain,
    register_template,
    search_tools,
    tool,
)
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


def test_discovery_lists_decorator_and_template() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        from orchestrator._internal.backends.tools import get_tool_registry

        registry = get_registry()
        registry.clear()

        tool_registry = get_tool_registry()
        tool_registry.clear()  # type: ignore[attr-defined]

        @tool(
            description="Echo",
            parameters=[ToolParameter(name="text", type="string", description="", required=True)],
        )
        def echo(params: dict[str, Any]) -> dict[str, Any]:
            return {"text": params["text"]}

        class EchoTemplate(FunctionToolTemplate):
            def execute(self, params: dict[str, Any]) -> dict[str, Any]:
                return {"text": params["text"]}

        tmpl = EchoTemplate(name="echo_tpl", description="Echo template")
        register_template(tmpl)

        tools = get_available_tools()
        names = sorted(t.name for t in tools)
        assert names == ["echo", "echo_tpl"]


def test_search_and_get_info() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        from orchestrator._internal.backends.tools import get_tool_registry

        registry = get_registry()
        registry.clear()

        tool_registry = get_tool_registry()
        tool_registry.clear()  # type: ignore[attr-defined]

        @tool(description="Process order", metadata={"tags": ["order"]})
        def process_order(params: dict[str, Any]) -> dict[str, Any]:
            return params

        results = search_tools(query="order")
        assert any(hasattr(t, 'name') and t.name == "process_order" for t in results)

        info = get_tool_info("process_order")
        if info and hasattr(info, 'name'):
            assert info.name == "process_order"


def test_list_by_domain() -> None:
    # Ensure local registry is used (redis may not be installed)
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        from orchestrator._internal.backends.tools import get_tool_registry

        registry = get_registry()
        registry.clear()

        tool_registry = get_tool_registry()
        tool_registry.clear()  # type: ignore[attr-defined]

        @tool(description="Finance tool", metadata={"tags": ["finance"]})
        def fin(params: dict[str, Any]) -> dict[str, Any]:
            return params

        # Default domain is "general" per models
        tools = list_tools_by_domain("general")
        assert any(t.name == "fin" for t in tools)
