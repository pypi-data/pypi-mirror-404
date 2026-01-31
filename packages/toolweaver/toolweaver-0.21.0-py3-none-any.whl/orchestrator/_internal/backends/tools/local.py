"""
Local Tool Registry

In-memory tool registry for local function registration.
Default implementation with zero dependencies.
"""

import logging
from collections.abc import Callable
from threading import Lock
from typing import Any

from .base import ToolError, ToolRegistry

logger = logging.getLogger(__name__)


class LocalToolRegistry(ToolRegistry):
    """
    In-memory tool registry using dictionaries.

    Tools and metadata stored in memory, thread-safe with locks.
    Perfect for single-process agent deployments.

    Example:
        registry = LocalToolRegistry()

        def search(query: str) -> str:
            return f"Results for: {query}"

        registry.register_tool("search", search, metadata={
            "description": "Search the web",
            "parameters": {"query": "string"}
        })

        tool = registry.get_tool("search")
        result = tool("Python tutorial")
    """

    def __init__(self) -> None:
        """Initialize local tool registry."""
        self._tools: dict[str, Callable[..., Any]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("Initialized LocalToolRegistry")

    def register_tool(
        self, name: str, tool: Callable[..., Any], metadata: dict[str, Any] | None = None, **kwargs: Any
    ) -> bool:
        """Register a tool in memory."""
        if not callable(tool):
            raise ToolError(f"Tool must be callable: {name}")

        with self._lock:
            if name in self._tools:
                logger.warning(f"Tool already registered, overwriting: {name}")

            self._tools[name] = tool
            self._metadata[name] = metadata or {}

        logger.info(f"Registered tool: {name}")
        return True

    def get_tool(self, name: str, **kwargs: Any) -> Callable[..., Any] | None:
        """Get tool from memory."""
        with self._lock:
            tool = self._tools.get(name)

        if tool:
            logger.debug(f"Retrieved tool: {name}")
        return tool

    def unregister_tool(self, name: str, **kwargs: Any) -> bool:
        """Remove tool from memory."""
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                del self._metadata[name]
                logger.info(f"Unregistered tool: {name}")
                return True
        return False

    def list_tools(self, category: str | None = None, **kwargs: Any) -> list[str]:
        """List all registered tool names."""
        with self._lock:
            tools = list(self._tools.keys())

            # Filter by category if specified
            if category:
                tools = [
                    name
                    for name in tools
                    if self._metadata.get(name, {}).get("category") == category
                ]

        return sorted(tools)

    def get_tool_metadata(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        """Get tool metadata from memory."""
        with self._lock:
            return self._metadata.get(name)

    def exists(self, name: str, **kwargs: Any) -> bool:
        """Check if tool exists in memory."""
        with self._lock:
            return name in self._tools

    def clear(self) -> None:
        """Clear all registered tools from memory."""
        with self._lock:
            self._tools.clear()
            self._metadata.clear()
        # logger.info("Cleared all tools from LocalToolRegistry")

    def __len__(self) -> int:
        """Return number of registered tools."""
        with self._lock:
            return len(self._tools)

    def __repr__(self) -> str:
        with self._lock:
            count = len(self._tools)
        return f"LocalToolRegistry(tools={count})"
