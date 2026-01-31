import json
import logging
import os
import sqlite3
from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from .base import ToolError, ToolRegistry

logger = logging.getLogger(__name__)


class SQLiteToolRegistry(ToolRegistry):
    """
    SQLite-backed tool registry.

    Stores metadata and import paths in SQLite; keeps callables in-memory cache
    for fast execution. On cache miss, attempts to re-import the callable using
    the stored import path.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path: str = db_path or os.getenv("ORCHESTRATOR_TOOL_DB", ".toolweaver/tools.db")  # type: ignore[assignment]
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tools (
                name TEXT PRIMARY KEY,
                metadata TEXT NOT NULL,
                import_path TEXT
            )
            """
        )
        self._conn.commit()

        self._tools: dict[str, Callable[..., Any]] = {}
        logger.info("Initialized SQLiteToolRegistry at %s", self.db_path)

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

        self._conn.execute(
            "INSERT INTO tools(name, metadata, import_path) VALUES(?, ?, ?)\n"
            "ON CONFLICT(name) DO UPDATE SET metadata=excluded.metadata, import_path=excluded.import_path",
            (name, json.dumps(meta), import_path),
        )
        self._conn.commit()

        logger.info("Registered tool in sqlite: %s", name)
        return True

    def get_tool(self, name: str, **kwargs: Any) -> Callable[..., Any] | None:
        if name in self._tools:
            return self._tools[name]

        row = self._conn.execute("SELECT import_path FROM tools WHERE name = ?", (name,)).fetchone()
        if not row:
            return None

        import_path = row[0]
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
        cur = self._conn.execute("DELETE FROM tools WHERE name = ?", (name,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_tools(self, category: str | None = None, **kwargs: Any) -> list[str]:
        rows = self._conn.execute("SELECT name, metadata FROM tools").fetchall()
        names: list[str] = []
        for name, metadata_json in rows:
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
        row = self._conn.execute("SELECT metadata FROM tools WHERE name = ?", (name,)).fetchone()
        if not row:
            return None
        try:
            return cast(dict[str, Any], json.loads(row[0]))
        except Exception:  # noqa: BLE001
            return None

    def exists(self, name: str, **kwargs: Any) -> bool:
        row = self._conn.execute("SELECT 1 FROM tools WHERE name = ?", (name,)).fetchone()
        return row is not None

    def clear(self) -> None:
        self._tools.clear()
        self._conn.execute("DELETE FROM tools")
        self._conn.commit()

    def __len__(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM tools").fetchone()
        return int(row[0]) if row else 0

    def __repr__(self) -> str:
        return f"SQLiteToolRegistry(db_path={self.db_path}, tools={len(self)})"


def _build_import_path(fn: Callable[..., Any]) -> str | None:
    module = getattr(fn, "__module__", None)
    qualname = getattr(fn, "__qualname__", None)
    if module and qualname and "<locals>" not in qualname:
        return f"{module}:{qualname}"
    return None
