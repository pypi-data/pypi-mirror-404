"""
Public API for tool registry access.

Users should import from this module instead of orchestrator._internal.backends.
This ensures a stable public API that won't change between versions.

Usage:
    from orchestrator import get_tool_registry

    registry = get_tool_registry()
    tools = registry.list_tools()
"""

from orchestrator._internal.backends.tools.base import get_tool_registry

__all__ = ["get_tool_registry"]
