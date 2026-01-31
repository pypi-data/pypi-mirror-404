"""
Tool Registry Package (DEPRECATED - use _internal.backends.tools).

Provides pluggable tool registries for agent tools.

Re-exports from new location for backwards compatibility.
"""

from orchestrator._internal.backends.tools.base import ToolError, ToolRegistry, get_tool_registry
from orchestrator._internal.backends.tools.local import LocalToolRegistry

__all__ = [
    "ToolRegistry",
    "ToolError",
    "get_tool_registry",
    "LocalToolRegistry",
]
