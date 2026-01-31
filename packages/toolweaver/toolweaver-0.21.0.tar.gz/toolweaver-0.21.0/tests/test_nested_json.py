import os
from typing import Any
from unittest.mock import patch

from orchestrator import FunctionToolTemplate, register_template, tool
from orchestrator._internal.backends.tools import get_tool_registry
from orchestrator.plugins.registry import get_registry


def test_decorator_supports_nested_input_schema() -> None:
    with patch.dict(os.environ, {"ORCHESTRATOR_TOOL_REGISTRY": "local"}, clear=False):
        registry = get_registry()
        registry.clear()

        local_registry = get_tool_registry("local")
        local_registry.clear()  # type: ignore[attr-defined]

        nested_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "profile": {
                            "type": "object",
                            "properties": {
                                "age": {"type": "integer"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["age"],
                        },
                    },
                    "required": ["id"],
                }
            },
            "required": ["user"],
        }

        @tool(description="Process nested user payload", input_schema=nested_schema)
        def process(params: dict[str, Any]) -> dict[str, Any]:
            return params

        # Tool is registered with local registry, check via __tool_definition__
        assert hasattr(process, "__tool_definition__")
        td = process.__tool_definition__
        assert td.name == "process"
        assert td.input_schema == nested_schema


def test_template_supports_nested_input_schema() -> None:
    registry = get_registry()
    registry.clear()

    nested_schema = {
        "type": "object",
        "properties": {
            "order": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {"type": "object", "properties": {"sku": {"type": "string"}}},
                    },
                },
                "required": ["id"],
            }
        },
        "required": ["order"],
    }

    class OrderTemplate(FunctionToolTemplate):
        def execute(self, params: dict[str, Any]) -> dict[str, Any]:
            return params

    tmpl = OrderTemplate(
        name="order_process", description="Process order", input_schema=nested_schema
    )
    register_template(tmpl)

    plugin = registry.get("templates")
    tools = plugin.get_tools()
    td = tools[0]
    assert td["name"] == "order_process"
    assert td["input_schema"] == nested_schema
