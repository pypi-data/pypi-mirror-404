import json
import logging
import os
from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import redis

from .base import ToolError, ToolRegistry

logger = logging.getLogger(__name__)


class RedisToolRegistry(ToolRegistry):
    """
    Redis-backed tool registry.

    Stores metadata and import paths in Redis; keeps callables in-memory cache
    for fast execution. On cache miss, attempts to re-import the callable using
    the stored import path.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str | None = None,
        password: str | None = None,
    ) -> None:
        self.redis_url = redis_url or os.getenv("ORCHESTRATOR_REDIS_URL", "redis://localhost:6379/0")
        self.namespace = namespace or os.getenv("ORCHESTRATOR_REDIS_NAMESPACE", "toolweaver")
        self.password = password or os.getenv("ORCHESTRATOR_REDIS_PASSWORD")
        self.client = redis.from_url(self.redis_url, password=self.password, decode_responses=True)
        self._tools: dict[str, Callable[..., Any]] = {}
        logger.info("Initialized RedisToolRegistry at %s (ns=%s)", self.redis_url, self.namespace)

    def _key(self, suffix: str) -> str:
        return f"{self.namespace}:{suffix}"

    def register_tool(
        self, name: str, tool: Callable[..., Any], metadata: dict[str, Any] | None = None, **kwargs: Any
    ) -> bool:
        if not callable(tool):
            raise ToolError(f"Tool must be callable: {name}")

        # Use original_function if provided (for decorated tools)
        original_fn = kwargs.get("original_function", tool)
        import_path = _build_import_path(original_fn)
        meta = metadata or {}
        meta["import_path"] = import_path

        self._tools[name] = tool

        pipe = self.client.pipeline()
        pipe.hset(self._key("tools:meta"), name, json.dumps(meta))
        if import_path:
            pipe.hset(self._key("tools:import"), name, import_path)
        pipe.execute()

        logger.info("Registered tool in redis: %s", name)
        return True

    def get_tool(self, name: str, **kwargs: Any) -> Callable[..., Any] | None:
        if name in self._tools:
            return self._tools[name]

        import_path = self.client.hget(self._key("tools:import"), name)
        if not import_path:
            return None

        try:
            module_path, func_name = import_path.rsplit(":", 1)
            module = import_module(module_path)
            fn = getattr(module, func_name)
            self._tools[name] = fn
            return cast(Callable[..., Any], fn)
        except Exception as exc:  # noqa: BLE001
            # Tools from __main__ can't be reimported; this is expected behavior
            if module_path == "__main__":
                logger.debug("Tool %s from __main__ cannot be reimported (expected): %s", name, exc)
            else:
                logger.error("Failed to import tool %s via %s: %s", name, import_path, exc)
            return None

    def unregister_tool(self, name: str, **kwargs: Any) -> bool:
        self._tools.pop(name, None)
        pipe = self.client.pipeline()
        pipe.hdel(self._key("tools:meta"), name)
        pipe.hdel(self._key("tools:import"), name)
        res = pipe.execute()
        return any(r for r in res)

    def list_tools(self, category: str | None = None, **kwargs: Any) -> list[str]:
        meta_map = self.client.hgetall(self._key("tools:meta"))
        names: list[str] = []
        for name, metadata_json in meta_map.items():
            if category:
                try:
                    md = json.loads(metadata_json)
                    if md.get("category") != category:
                        continue
                except Exception:  # noqa: BLE001
                    continue
            names.append(name)
        return sorted(names)

    def get_tool_metadata(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        data = self.client.hget(self._key("tools:meta"), name)
        if not data:
            return None
        try:
            return cast(dict[str, Any], json.loads(data))
        except Exception:  # noqa: BLE001
            return None

    def exists(self, name: str, **kwargs: Any) -> bool:
        return bool(self.client.hexists(self._key("tools:meta"), name))

    def clear(self) -> None:
        pipe = self.client.pipeline()
        pipe.delete(self._key("tools:meta"))
        pipe.delete(self._key("tools:import"))
        pipe.execute()
        self._tools.clear()

    def __len__(self) -> int:
        return int(self.client.hlen(self._key("tools:meta")))

    def __repr__(self) -> str:
        return f"RedisToolRegistry(url={self.redis_url}, ns={self.namespace}, tools={len(self)})"


def _build_import_path(fn: Callable[..., Any]) -> str | None:
    module = getattr(fn, "__module__", None)
    qualname = getattr(fn, "__qualname__", None)
    if module and qualname and "<locals>" not in qualname:
        return f"{module}:{qualname}"
    return None
