"""
Tools and Search subpackage.

Consolidates tool discovery, execution, filesystem management, semantic search, and stdlib tools.
"""

from .decorators import (
    a2a_agent,
    execute_tool,
    execute_tool_async,
    get_all_registered_tools,
    get_tool_by_name,
    get_tool_definition,
    list_tools_by_domain,
    list_tools_by_type,
    mcp_tool,
    tool,
)
from .tool_discovery import (
    CodeExecToolDiscoverer,
    DiscoveryMetrics,
    FunctionToolDiscoverer,
    MCPToolDiscoverer,
    ToolDiscoveryOrchestrator,
    ToolDiscoveryService,
    discover_tools,
)
from .tool_executor import call_tool
from .tool_filesystem import (
    ToolFileSystem,
    ToolInfo,
)

# Optional: Search tools (require numpy, sentence-transformers)
try:
    from .tool_search import ToolSearchEngine, search_tools
    from .tool_search_tool import (
        get_tool_search_definition,
        initialize_tool_search,
        tool_search_tool,
    )
    from .vector_search import VectorToolSearchEngine

    _SEARCH_AVAILABLE = True
except ImportError:
    _SEARCH_AVAILABLE = False

from .mcp_subprocess import (
    MCPServerConfig,
    MCPSubprocessClient,
    MCPSubprocessContext,
)
from .sharded_catalog import ShardedCatalog

# Stdlib tools (available by default)
try:
    from . import stdlib
    from .stdlib import (
        bash,
        code_exec,
        memory_get,
        memory_put,
        register_stdlib_tools,
        text_edit,
        tool_search,
        web_fetch,
        web_search,
    )

    _STDLIB_AVAILABLE = True
except ImportError:
    _STDLIB_AVAILABLE = False

__all__ = [
    # Decorators & registration (Phase 0)
    "tool",
    "mcp_tool",
    "a2a_agent",
    "get_all_registered_tools",
    "get_tool_by_name",
    "execute_tool",
    "execute_tool_async",
    "list_tools_by_type",
    "list_tools_by_domain",
    "get_tool_definition",
    # Discovery & execution
    "ToolDiscoveryService",
    "ToolDiscoveryOrchestrator",
    "MCPToolDiscoverer",
    "FunctionToolDiscoverer",
    "CodeExecToolDiscoverer",
    "DiscoveryMetrics",
    "discover_tools",
    "call_tool",
    "ToolFileSystem",
    "ToolInfo",
    "ShardedCatalog",
    # MCP Subprocess Client (NEW - generic MCP integration)
    "MCPServerConfig",
    "MCPSubprocessClient",
    "MCPSubprocessContext",
]

if _SEARCH_AVAILABLE:
    __all__.extend(
        [
            "ToolSearchEngine",
            "search_tools",
            "tool_search_tool",
            "initialize_tool_search",
            "get_tool_search_definition",
            "VectorToolSearchEngine",
        ]
    )

if _STDLIB_AVAILABLE:
    __all__.extend(
        [
            "stdlib",
            "web_search",
            "web_fetch",
            "memory_get",
            "memory_put",
            "tool_search",
            "bash",
            "code_exec",
            "text_edit",
            "register_stdlib_tools",
        ]
    )
