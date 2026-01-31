"""
Tool Registry - Abstract Base Class

Defines the interface for registering and managing agent tools.
Tools are callable functions that agents can invoke.

Phase 2: In-memory registry, MCP tools
Phase 5: API-based tools, database-backed registry
"""

import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, cast

logger = logging.getLogger(__name__)

# Global cache for singleton registries (local registry only)
_registry_cache: dict[str, Any] = {}


class ToolError(Exception):
    """Raised when tool operations fail."""

    pass


class ToolRegistry(ABC):
    """
    Abstract base class for tool registration strategies.

    Tools are functions that agents can call to perform actions.
    Different implementations support local, MCP, API, or composite tools.

    Example:
        registry = get_tool_registry("local")
        registry.register_tool("search", search_function)
        tool = registry.get_tool("search")
        result = tool("python tutorial")
    """

    @abstractmethod
    def register_tool(
        self, name: str, tool: Callable[..., Any], metadata: dict[str, Any] | None = None, **kwargs: Any
    ) -> bool:
        """
        Register a tool function.

        Args:
            name: Unique tool identifier
            tool: Callable function implementing the tool
            metadata: Optional tool metadata (description, parameters, etc.)
            **kwargs: Implementation-specific options

        Returns:
            True if registered, False if already exists

        Raises:
            ToolError: If registration fails
        """
        pass

    @abstractmethod
    def get_tool(self, name: str, **kwargs: Any) -> Callable[..., Any] | None:
        """
        Get a registered tool by name.

        Args:
            name: Tool identifier
            **kwargs: Implementation-specific options

        Returns:
            Tool callable or None if not found
        """
        pass

    @abstractmethod
    def unregister_tool(self, name: str, **kwargs: Any) -> bool:
        """
        Remove a tool from registry.

        Args:
            name: Tool identifier
            **kwargs: Implementation-specific options

        Returns:
            True if removed, False if not found
        """
        pass

    @abstractmethod
    def list_tools(self, category: str | None = None, **kwargs: Any) -> list[str]:
        """
        List registered tool names.

        Args:
            category: Optional category filter
            **kwargs: Implementation-specific options

        Returns:
            List of tool names
        """
        pass

    @abstractmethod
    def get_tool_metadata(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        """
        Get metadata for a tool.

        Args:
            name: Tool identifier
            **kwargs: Implementation-specific options

        Returns:
            Tool metadata dictionary or None if not found
        """
        pass

    @abstractmethod
    def exists(self, name: str, **kwargs: Any) -> bool:
        """
        Check if a tool is registered.

        Args:
            name: Tool identifier
            **kwargs: Implementation-specific options

        Returns:
            True if tool exists, False otherwise
        """
        pass


def get_tool_registry(registry_type: str | None = None, **kwargs: Any) -> ToolRegistry:
    """
    Factory function to get tool registry instance.

    Chooses backend from env `ORCHESTRATOR_TOOL_REGISTRY` when not provided.
    Supports: local (default), sqlite, redis.
    """
    from .local import LocalToolRegistry

    env_choice = os.getenv("ORCHESTRATOR_TOOL_REGISTRY")
    registry_type = (registry_type or env_choice or "local").lower()

    # For local registry, use singleton pattern
    if registry_type == "local":
        if "local" not in _registry_cache:
            _registry_cache["local"] = LocalToolRegistry()
        return cast(ToolRegistry, _registry_cache["local"])

    registries: dict[str, type[ToolRegistry]] = {"local": LocalToolRegistry}

    try:
        from .sqlite import SQLiteToolRegistry

        if registry_type == "sqlite":
            db_path = kwargs.get("db_path") or os.getenv("ORCHESTRATOR_TOOL_DB", ".toolweaver/tools.db")
            cache_key = f"sqlite:{db_path}"
            if cache_key not in _registry_cache:
                _registry_cache[cache_key] = SQLiteToolRegistry(db_path=db_path)
            return cast(ToolRegistry, _registry_cache[cache_key])

        registries["sqlite"] = SQLiteToolRegistry
    except Exception:  # noqa: BLE001 - optional backend
        pass

    try:
        from .redis_registry import RedisToolRegistry

        if registry_type == "redis":
            redis_url = kwargs.get("redis_url") or os.getenv("ORCHESTRATOR_REDIS_URL", "redis://localhost:6379/0")
            namespace = kwargs.get("namespace") or os.getenv("ORCHESTRATOR_REDIS_NAMESPACE", "toolweaver")
            password = kwargs.get("password") or os.getenv("ORCHESTRATOR_REDIS_PASSWORD")
            cache_key = f"redis:{redis_url}:{namespace}"
            if cache_key not in _registry_cache:
                _registry_cache[cache_key] = RedisToolRegistry(
                    redis_url=redis_url,
                    namespace=namespace,
                    password=password,
                )
            return cast(ToolRegistry, _registry_cache[cache_key])

        registries["redis"] = RedisToolRegistry
    except Exception:  # noqa: BLE001 - optional backend
        pass

    registry_class = registries.get(registry_type)
    if not registry_class:
        available = ", ".join(sorted(registries.keys()))
        raise ValueError(
            f"Unknown registry type: {registry_type}. Available registries: {available}"
        )

    try:
        return registry_class(**kwargs)
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"Failed to initialize {registry_type} registry: {e}") from e
