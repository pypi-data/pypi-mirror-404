"""Tool Registry Implementations

Abstract: ToolRegistry (base.py)
Implementations:
- LocalToolRegistry - Local tool discovery and registration

Phase 1+: MCP server tools, API-based tools, plugin-based tools
"""

from orchestrator._internal.backends.tools.base import ToolRegistry, get_tool_registry
from orchestrator._internal.backends.tools.local import LocalToolRegistry

try:
    from orchestrator._internal.backends.tools.sqlite import SQLiteToolRegistry
except Exception:  # noqa: BLE001 - optional backend
    SQLiteToolRegistry = None  # type: ignore

try:
    from orchestrator._internal.backends.tools.redis_registry import RedisToolRegistry
except Exception:  # noqa: BLE001 - optional backend
    RedisToolRegistry = None  # type: ignore

__all__ = [
    "ToolRegistry",
    "LocalToolRegistry",
    "SQLiteToolRegistry",
    "RedisToolRegistry",
    "get_tool_registry",
]
