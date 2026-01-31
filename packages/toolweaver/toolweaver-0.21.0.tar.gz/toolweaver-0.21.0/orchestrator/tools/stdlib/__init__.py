"""
ToolWeaver Standard Library Tools (stdlib).

Core tools (enabled by default):
    - web_search(query, k=5, lang="en"): Search the web
    - web_fetch(url, timeout_s=10, max_bytes=20000): Fetch URL content
    - memory_put(key, value, ttl_s=None): Store session value
    - memory_get(key): Retrieve session value
    - tool_search(query, top_k=5, tags=None): Search for available tools

Guarded tools (disabled by default, opt-in required):
    - bash(command, timeout_s=10, allowlist_paths=None): Execute bash command
    - code_exec(language, source, timeout_s=10): Execute code
    - text_edit(path, op, content="", allowlist_paths=None): Edit files

All tools include RLM hooks (pre-call validation, post-call truncation/redaction).

Configuration via environment variables:
    TOOLWEAVER_STDLIB_ENABLED: Comma-separated list of enabled core tools
                               (default: "web_search,web_fetch,memory,tool_search")
    TOOLWEAVER_STDLIB_DISABLED: Comma-separated list of disabled core tools (overrides enabled list)
    TOOLWEAVER_STDLIB_GUARDED_ENABLED: Comma-separated list of enabled guarded tools
                                       (default: "")
    TOOLWEAVER_STDLIB_<TOOL>_ENABLED: Override individual tool (e.g., TOOLWEAVER_STDLIB_WEB_SEARCH_ENABLED=false)
                                      <TOOL> keys use normalized names (WEB_SEARCH, WEB_FETCH, MEMORY, TOOL_SEARCH)

Example:
    from orchestrator.tools.stdlib import register_stdlib_tools
    from orchestrator import execute_plan

    # Register all enabled stdlib tools
    register_stdlib_tools()

    # Now planner can use them
    plan = [
        {"tool": "web_search", "args": {"query": "latest AI news"}},
        {"tool": "web_fetch", "args": {"url": "https://example.com"}},
        {"tool": "memory_put", "args": {"key": "result", "value": {...}}},
    ]
    result = await execute_plan(plan)
"""

from __future__ import annotations

import logging
from typing import Any

from . import core_tools, guarded_tools
from .bash_providers import (
    BashProvider,
    get_bash_provider,
    register_bash_provider,
)
from .code_exec_providers import (
    CodeExecProvider,
    get_code_exec_provider,
    register_code_exec_provider,
)
from .core_tools import (
    memory_get,
    memory_put,
    tool_search,
    web_fetch,
    web_search,
)
from .fetch_providers import (
    FetchProvider,
    get_fetch_provider,
    register_fetch_provider,
)
from .guarded_tools import bash, code_exec, text_edit
from .memory_providers import (
    MemoryProvider,
    get_memory_provider,
    register_memory_provider,
)
from .provider_router import (
    CircuitBreaker,
    ProviderRouter,
    RateLimiter,
    RouterStrategy,
)
from .search_providers import (
    SearchProvider,
    get_search_provider,
    register_search_provider,
)
from .text_edit_providers import (
    TextEditProvider,
    get_text_edit_provider,
    register_text_edit_provider,
)
from .tool_search_providers import (
    ToolSearchProvider,
    get_tool_search_provider,
    register_tool_search_provider,
)

logger = logging.getLogger(__name__)

__all__ = [
    # Core tools
    "web_search",
    "web_fetch",
    "memory_get",
    "memory_put",
    "tool_search",
    # Guarded tools
    "bash",
    "code_exec",
    "text_edit",
    # Registration
    "register_stdlib_tools",
    # Search provider adapter pattern
    "SearchProvider",
    "register_search_provider",
    "get_search_provider",
    # Fetch provider adapter pattern
    "FetchProvider",
    "register_fetch_provider",
    "get_fetch_provider",
    # Memory provider adapter pattern
    "MemoryProvider",
    "register_memory_provider",
    "get_memory_provider",
    # Tool search provider adapter pattern
    "ToolSearchProvider",
    "register_tool_search_provider",
    "get_tool_search_provider",
    # Bash provider adapter pattern
    "BashProvider",
    "register_bash_provider",
    "get_bash_provider",
    # Code exec provider adapter pattern
    "CodeExecProvider",
    "register_code_exec_provider",
    "get_code_exec_provider",
    # Text edit provider adapter pattern
    "TextEditProvider",
    "register_text_edit_provider",
    "get_text_edit_provider",
    # Provider router (fallback, load balancing)
    "ProviderRouter",
    "RouterStrategy",
    "CircuitBreaker",
    "RateLimiter",
]


def register_stdlib_tools() -> None:
    """
    Register all enabled stdlib tools as MCP tools.

    This should be called early during app initialization to make tools
    available to discovery, planner, and execution.

    Respects configuration:
        - TOOLWEAVER_STDLIB_ENABLED for core tools
        - TOOLWEAVER_STDLIB_GUARDED_ENABLED for guarded tools
        - Individual tool _ENABLED flags override
    """
    from orchestrator.tools.decorators import mcp_tool

    # Core tools to register
    core_tools_list: list[tuple[str, Any, str]] = [
        ("web_search", web_search, "Search the web for information"),
        ("web_fetch", web_fetch, "Fetch content from a URL"),
        ("memory_get", memory_get, "Retrieve a value from session memory"),
        ("memory_put", memory_put, "Store a value in session memory with optional TTL"),
        ("tool_search", tool_search, "Search for available tools by name/description"),
    ]

    for tool_name, tool_func, description in core_tools_list:
        if core_tools._is_tool_enabled(tool_name):
            # Wrap as MCP tool via decorator
            mcp_tool(name=tool_name, description=description, domain="stdlib")(
                tool_func
            )
            logger.debug(f"Registered stdlib tool: {tool_name}")

    # Guarded tools to register
    guarded_tools_list: list[tuple[str, Any, str]] = [
        ("bash", bash, "Execute a bash command (GUARDED - requires explicit opt-in)"),
        ("code_exec", code_exec, "Execute code in a sandbox (GUARDED - requires explicit opt-in)"),
        (
            "text_edit",
            text_edit,
            "Edit files on disk (GUARDED - requires explicit opt-in)",
        ),
    ]

    for tool_name, tool_func, description in guarded_tools_list:
        if guarded_tools._is_guarded_enabled(tool_name):
            # Wrap as MCP tool via decorator
            mcp_tool(name=tool_name, description=description, domain="stdlib-guarded")(
                tool_func
            )
            logger.debug(f"Registered guarded stdlib tool: {tool_name}")
