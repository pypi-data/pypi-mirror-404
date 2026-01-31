from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any, Literal, cast, get_args, get_origin

from ..shared.models import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)


def _get_tool_registry() -> Any:
    """Get tool registry from Phase -1 backends (single source of truth)."""
    from .._internal.backends.tools import get_tool_registry

    return get_tool_registry()


def tool(
    *,
    name: str | None = None,
    description: str = "",
    provider: str | None = None,
    type: Literal["mcp", "function", "code_exec", "agent", "tool"] = "function",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to declare a function as a ToolWeaver tool.

    Example:
        @tool(description="Echo input", parameters=[ToolParameter(name="text", type="string", required=True, description="Text to echo")])
        def echo(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"text": params["text"]}
    """

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="function",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=False)

    return wrapper


def mcp_tool(
    *,
    name: str | None = None,
    description: str = "",
    provider: str | None = "mcp",
    domain: str = "general",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for MCP tools with auto parameter extraction from type hints."""

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="mcp",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
            domain=domain,
            returns=_infer_returns_schema(fn),
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=True)

    return wrapper


def a2a_agent(
    *,
    name: str | None = None,
    description: str = "",
    provider: str | None = "a2a",
    domain: str = "general",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for agent (A2A) tools with auto parameter extraction."""

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="agent",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
            domain=domain,
            returns=_infer_returns_schema(fn),
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=True)

    return wrapper


def _register_bound_function(
    *,
    fn: Callable[..., Any],
    tool_def: ToolDefinition,
    expects_kwargs: bool,
) -> Callable[[dict[str, Any]], Any]:
    """Register bound function to Phase -1 ToolRegistry backend."""
    registry = _get_tool_registry()

    _validate_tool_signature(fn=fn, tool_def=tool_def, expects_kwargs=expects_kwargs)

    async def bound(params: dict[str, Any]) -> Any:
        call_params = params or {}
        try:
            result = fn(**call_params) if expects_kwargs else fn(call_params)
        except TypeError as exc:  # surface clearer error for bad calls
            raise TypeError(f"Failed to execute tool '{tool_def.name}': {exc}") from exc

        if inspect.isawaitable(result):
            return await result
        return result

    bound.__wrapped__ = fn  # type: ignore
    bound.__tool_definition__ = tool_def  # type: ignore

    # Register to Phase -1 ToolRegistry backend
    # Pass original function for import path extraction
    registry.register_tool(
        name=tool_def.name,
        tool=bound,
        metadata={
            "description": tool_def.description,
            "type": tool_def.type,
            "provider": tool_def.provider,
            "domain": getattr(tool_def, "domain", "general"),
            "parameters": [p.model_dump() for p in tool_def.parameters]
            if tool_def.parameters
            else [],
        },
        original_function=fn,  # For import path extraction
    )

    # Log tool registration
    logger.info(
        f"Tool registered: {tool_def.name}",
        extra={
            "tool_name": tool_def.name,
            "tool_type": tool_def.type,
            "provider": tool_def.provider,
            "domain": getattr(tool_def, "domain", "general"),
            "param_count": len(tool_def.parameters) if tool_def.parameters else 0,
            "backend": "phase-minus-1-tool-registry",
        },
    )

    return bound


def _validate_tool_signature(
    *, fn: Callable[..., Any], tool_def: ToolDefinition, expects_kwargs: bool
) -> None:
    """Validate decorator usage and surface helpful warnings/errors."""
    sig = inspect.signature(fn)

    # Missing docstring
    if not (fn.__doc__ or "").strip():
        logger.warning("Tool '%s' is missing a docstring", tool_def.name)

    # Missing return annotation
    if sig.return_annotation is inspect.Signature.empty:
        logger.warning("Tool '%s' is missing a return type annotation", tool_def.name)

    # Missing parameter annotations
    missing_param_annotations = [
        p.name for p in sig.parameters.values() if p.annotation is inspect.Signature.empty
    ]
    if missing_param_annotations:
        logger.warning(
            "Tool '%s' parameters missing type hints: %s",
            tool_def.name,
            ", ".join(missing_param_annotations),
        )

    # Invalid parameter names (fail fast)
    param_names = [p.name for p in sig.parameters.values()]
    invalid = [name for name in param_names if not name.isidentifier()]
    if invalid:
        raise ValueError(
            f"Tool '{tool_def.name}' has invalid parameter names: {', '.join(invalid)}"
        )

    # Ensure provided ToolParameters align with function signature when using kwargs
    if expects_kwargs and tool_def.parameters:
        provided_names = {p.name for p in tool_def.parameters}
        missing_in_params = [n for n in param_names if n not in provided_names]
        if missing_in_params:
            raise ValueError(
                f"Tool '{tool_def.name}' parameter mismatch: signature has {missing_in_params}"
            )


def _infer_parameters_from_signature(fn: Callable[..., Any]) -> list[ToolParameter]:
    sig = inspect.signature(fn)
    inferred: list[ToolParameter] = []

    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        annotation = param.annotation
        param_type = _map_annotation_to_param_type(annotation)
        optional = _is_optional_annotation(annotation)
        required = param.default is inspect._empty and not optional

        inferred.append(
            ToolParameter(
                name=name,
                type=param_type,
                description="",
                required=required,
            )
        )

    return inferred


def _infer_returns_schema(fn: Callable[..., Any]) -> dict[str, Any] | None:
    annotation = getattr(fn, "__annotations__", {}).get("return", inspect._empty)
    if annotation is inspect._empty:
        return None
    return {"type": _map_annotation_to_param_type(annotation)}


def _map_annotation_to_param_type(annotation: Any) -> str:
    if annotation is inspect._empty:
        return "string"

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is list or origin is list:
        return "array"
    if origin is dict or origin is dict:
        return "object"
    if origin in (tuple, set):
        return "array"
    if origin is None and annotation is None:
        return "string"

    if origin is not None:
        non_none_args = [a for a in args if a is not type(None)]  # noqa: E721
        if non_none_args:
            return _map_annotation_to_param_type(non_none_args[0])

    if annotation in (str,):
        return "string"
    if annotation in (int,):
        return "integer"
    if annotation in (float,):
        return "number"
    if annotation in (bool,):
        return "boolean"
    if annotation in (dict, dict):
        return "object"
    if annotation in (list, list, tuple, set):
        return "array"

    return "string"


def _is_optional_annotation(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is None:
        return False
    args = get_args(annotation)
    return any(arg is type(None) for arg in args)  # noqa: E721


# ============================================================================
# Helper Functions for Tool Discovery & Execution (Phase 0)
# ============================================================================


def get_all_registered_tools() -> dict[str, ToolDefinition]:
    """
    Get all tools registered via @tool, @mcp_tool, @a2a_agent decorators.

    Returns:
        Dictionary mapping tool name → ToolDefinition

    Example:
        @tool(description="Echo input")
        def echo(params):
            return {"text": params["text"]}

        tools = get_all_registered_tools()
        assert "echo" in tools
        assert tools["echo"].description == "Echo input"
    """
    registry = _get_tool_registry()
    tools_dict = {}

    for tool_name in registry.list_tools():
        tool_fn = registry.get_tool(tool_name)
        if tool_fn and hasattr(tool_fn, "__tool_definition__"):
            tool_def = tool_fn.__tool_definition__
            tools_dict[tool_name] = tool_def

    return tools_dict


def get_tool_by_name(name: str) -> Callable[..., Any]:
    """
    Get registered tool function by name.

    Args:
        name: Tool name to look up

    Returns:
        Callable tool function

    Raises:
        ValueError: If tool not found

    Example:
        @tool(description="Add numbers")
        def add_numbers(params):
            return {"result": params["a"] + params["b"]}

        tool = get_tool_by_name("add_numbers")
        result = tool({"a": 5, "b": 3})
        assert result["result"] == 8
    """
    registry = _get_tool_registry()
    tool = registry.get_tool(name)
    if not tool:
        raise ValueError(f"Tool not found: {name}")
    return cast(Callable[..., Any], tool)


def execute_tool(name: str, params: dict[str, Any]) -> Any:
    """
    Execute registered tool by name with parameters.

    Args:
        name: Tool name to execute
        params: Parameters dict to pass to tool

    Returns:
        Tool execution result

    Raises:
        ValueError: If tool not found
        TypeError: If tool execution fails

    Example:
        @mcp_tool(description="Calculate tax")
        def calculate_tax(amount: float, rate: float):
            return {"tax": amount * rate}

        result = execute_tool("calculate_tax", {"amount": 100, "rate": 0.1})
        assert result["tax"] == 10.0
    """
    tool = get_tool_by_name(name)
    result = tool(params)

    # Handle async functions
    if inspect.isawaitable(result):
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't use run() on running loop, would need proper async context
                raise RuntimeError(
                    f"Cannot execute async tool '{name}' from sync context. "
                    "Use 'await execute_tool_async()' instead."
                )
            return loop.run_until_complete(result)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(result)  # type: ignore[arg-type]

    return result


async def execute_tool_async(name: str, params: dict[str, Any]) -> Any:
    """
    Execute registered tool by name with parameters (async version).

    Args:
        name: Tool name to execute
        params: Parameters dict to pass to tool

    Returns:
        Tool execution result (awaited if async)

    Raises:
        ValueError: If tool not found

    Example:
        @mcp_tool(description="Fetch data")
        async def fetch_data(query: str):
            # async work
            return {"data": []}

        result = await execute_tool_async("fetch_data", {"query": "python"})
    """
    tool = get_tool_by_name(name)
    result = tool(params)

    if inspect.isawaitable(result):
        return await result

    return result


def list_tools_by_type(tool_type: str) -> list[str]:
    """
    List all registered tools of a specific type.

    Args:
        tool_type: Type to filter by ("function", "mcp", "agent", etc.)

    Returns:
        List of tool names matching the type

    Example:
        @tool(description="Tool1")
        def tool1(params):
            pass

        @mcp_tool(description="Tool2")
        def tool2(params):
            pass

        func_tools = list_tools_by_type("function")
        mcp_tools = list_tools_by_type("mcp")
        assert "tool1" in func_tools
        assert "tool2" in mcp_tools
    """
    all_tools = get_all_registered_tools()
    return [name for name, tool_def in all_tools.items() if tool_def.type == tool_type]


def list_tools_by_domain(domain: str) -> list[str]:
    """
    List all registered tools in a specific domain.

    Args:
        domain: Domain to filter by ("finance", "search", etc.)

    Returns:
        List of tool names in the domain

    Example:
        @mcp_tool(domain="finance", description="Calculate tax")
        def calculate_tax(amount: float):
            return {"tax": amount * 0.1}

        @mcp_tool(domain="search", description="Search web")
        def search(query: str):
            return {"results": []}

        finance_tools = list_tools_by_domain("finance")
        assert "calculate_tax" in finance_tools
    """
    all_tools = get_all_registered_tools()
    return [
        name
        for name, tool_def in all_tools.items()
        if getattr(tool_def, "domain", "general") == domain
    ]


def get_tool_definition(name: str) -> ToolDefinition:
    """
    Get tool definition (metadata) by name.

    Args:
        name: Tool name

    Returns:
        ToolDefinition with all metadata

    Raises:
        ValueError: If tool not found

    Example:
        @mcp_tool(
            description="Calculate tax",
            domain="finance",
            metadata={"version": "1.0"}
        )
        def calculate_tax(amount: float):
            return {"tax": amount * 0.1}

        tool_def = get_tool_definition("calculate_tax")
        assert tool_def.type == "mcp"
        assert tool_def.domain == "finance"
    """
    all_tools = get_all_registered_tools()
    if name not in all_tools:
        raise ValueError(f"Tool not found: {name}")
    return all_tools[name]
