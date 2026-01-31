"""
ToolWeaver - Package-first tool orchestration library.

A lightweight, composable package for registering and managing tools
that can be called by LLMs, APIs, CLI, or any Python application.

Philosophy: Users pip install toolweaver and use it in their own apps.
Not a framework--you control your architecture.

Package Users:
    from orchestrator import mcp_tool, search_tools

    @mcp_tool(domain="finance")
    async def get_balance(account: str) -> dict: ...

Contributors:
    Modify source via PR to add core features.
    Everything else is in orchestrator._internal (not part of public API).
"""

# MUST be first: Load .env before importing any other modules
import io
import logging
import os
import sys
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Optional, Protocol, Union

from . import _env_loader  # noqa: F401

# Initialize SILENT_MODE early if enabled
if os.getenv("SILENT_MODE", "").lower() in ("true", "1", "yes"):
    # Suppress all loggers immediately
    for logger_name in ["litellm", "openai", "azure", "orchestrator", "anthropic"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        # Remove all handlers to prevent output
        logger.handlers.clear()
        # Prevent propagation to parent
        logger.propagate = False
    # Suppress root logger for all other libraries
    logging.getLogger().setLevel(logging.CRITICAL)

    # Store original stdout/stderr for later restoration
    _original_stdout = sys.stdout
    _original_stderr = sys.stderr
    # Replace with null stream to suppress print() statements from libraries like LiteLLM
    _null_stream = io.StringIO()
    sys.stdout = _null_stream
    sys.stderr = _null_stream

__version__ = "1.0.0"


# ============================================================
# Phase 0 (Package Infrastructure) - Clean Public API
# ============================================================
# Only export what users should use. Everything else lives in _internal.
# This makes it clear what's safe to import and what might change.

# === Core Tool Registration (Phase 2) ===
# Phase 2: Decorators available for function, MCP, and agent tools
# === Agent-to-Agent (A2A) Client (Phase 1.7) ===
# [OK] DONE: Agent delegation and discovery
# === Skill Bridge (Phase 1.5) ===
# [OK] DONE: Phase 1.5 complete - Connect tools to skill library
# === Assessment & Evaluation (Phase 0.a) ===
# [OK] DONE: Agent evaluation and benchmarking
from ._internal.assessment.evaluation import AgentEvaluator
from ._internal.backends.observability.context_tracker import ContextTracker

# === MCP Client (Phase 1) ===
# [OK] DONE: MCP tool execution and registration
from ._internal.dispatch.lazy_registry import (
    register_example_functions,
    register_weather_adapter,
)
from ._internal.execution import skill_library

# === Code Generation & Stubs (Phase 1.11) ===
# [OK] DONE: Code stub generation for progressive tool discovery
from ._internal.execution.code_generator import StubGenerator
from ._internal.execution.programmatic_executor import ProgrammaticToolExecutor

# === Sandbox Execution (Phase 1.8) ===
# [OK] DONE: Sandboxed code execution
from ._internal.execution.sandbox import (
    ResourceLimits,
    SandboxEnvironment,
    SandboxSecurityError,
)
from ._internal.infra.a2a_client import (
    A2AClient,
    AgentCapability,
    AgentDelegationRequest,
    AgentDelegationResponse,
)
from ._internal.infra.function_gemma_validator import FunctionGemmaValidator
from ._internal.infra.mcp_auth import MCPAuthConfig
from ._internal.infra.mcp_client import MCPClientShim

# === Logging (Phase 0.l) ===
# [OK] DONE: Phase 0.l complete
from ._internal.logger import enable_debug_mode, get_logger, set_log_level

# === Planning (Phase 1.9) ===
# [OK] DONE: Large model planning
from ._internal.planning.planner import LargePlanner

# === Runtime Orchestration (Phase 1.10) ===
# [OK] DONE: Plan execution orchestrator
from ._internal.runtime.orchestrator import execute_plan, final_synthesis, run_step
from ._internal.security.secrets_redactor import install_secrets_redactor

# === Control Flow Patterns (Phase 2) ===
# [OK] DONE: Pattern library for code generation
from ._internal.workflows import (
    ControlFlowPatterns,
    create_conditional_code,
    create_parallel_code,
    create_polling_code,
    create_retry_code,
)

# === Configuration (Phase 0.c) ===
# [OK] DONE: Phase 0.c complete - Environment variable configuration
from .config import get_config, reset_config, validate_config
from .observability import Observability, get_observability

# === Plugin Registry (Phase 0.e) ===
# [OK] DONE: Phase 0.e complete - Plugin system for 3rd-party extensions
from .plugins import discover_plugins, get_plugin, list_plugins, register_plugin, unregister_plugin
from .selection import choose_model, route_request, set_available_models
from .tools.decorators import a2a_agent, get_all_registered_tools, mcp_tool, tool
from .tools.discovery_api import (
    browse_tools,
    get_available_tools,
    get_tool_info,
    list_tools_by_domain,
    search_tools,
    semantic_search_tools,
)

# === YAML Loader (Phase 3) ===
# [OK] DONE: Phase 3 complete - YAML-based tool registration
from .tools.loaders import (
    WorkerResolutionError,
    YAMLLoaderError,
    YAMLValidationError,
    load_tools_from_directory,
    load_tools_from_yaml,
)
from .tools.registry import get_tool_registry
from .tools.sharded_catalog import ShardedCatalog
from .tools.skill_bridge import (
    get_skill_backed_tools,
    get_tool_skill,
    load_tool_from_skill,
    save_tool_as_skill,
    sync_tool_with_skill,
)
from .tools.templates import (
    AgentTemplate,
    BaseTemplate,
    CodeExecToolTemplate,
    FunctionToolTemplate,
    MCPToolTemplate,
    register_template,
)
from .tools.tool_filesystem import ToolFileSystem

# === Mini DSL Executor (Phase 2) ===
# [OK] DONE: Declarative workflow composition with JSON/YAML specs
from .workflow import MiniDSLExecutor

# Heavy ML worker omitted during lightweight API startup; load on demand if needed
SmallModelWorker = None

# ============================================================
# Public API Definition
# ============================================================
# This is what users can safely import.
# Anything not listed here might change between versions.

# Restore stdout/stderr after all imports if SILENT_MODE was active
# This allows print() to work in user code while keeping LiteLLM quiet
if os.getenv("SILENT_MODE", "").lower() in ("true", "1", "yes"):
    if "_original_stdout" in locals():
        sys.stdout = _original_stdout
        sys.stderr = _original_stderr

__all__ = [
    # Version
    "__version__",
    # Core Decorators (Phase 2)
    "tool",
    "mcp_tool",
    "a2a_agent",
    "get_all_registered_tools",
    # Template Classes (Phase 1)
    "BaseTemplate",
    "FunctionToolTemplate",
    "MCPToolTemplate",
    "CodeExecToolTemplate",
    "AgentTemplate",
    "register_template",
    # YAML Loader (Phase 3)
    "load_tools_from_yaml",
    "load_tools_from_directory",
    "YAMLLoaderError",
    "YAMLValidationError",
    "WorkerResolutionError",
    # Skill Bridge (Phase 1.5)
    "save_tool_as_skill",
    "load_tool_from_skill",
    "get_tool_skill",
    "sync_tool_with_skill",
    "get_skill_backed_tools",
    # Discovery API (Phase 1.6)
    "get_available_tools",
    "search_tools",
    "get_tool_info",
    "list_tools_by_domain",
    "semantic_search_tools",
    "browse_tools",
    "get_tool_registry",
    # Plugins (Phase 0.e)
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "discover_plugins",
    # Configuration (Phase 0.c)
    "get_config",
    "reset_config",
    "validate_config",
    # Logging (Phase 0.l)
    "get_logger",
    "set_log_level",
    "enable_debug_mode",
    "Observability",
    "get_observability",
    # Agent-to-Agent (A2A) Client (Phase 1.7)
    "AgentCapability",
    "AgentDelegationRequest",
    "AgentDelegationResponse",
    "A2AClient",
    # MCP Client (Phase 1)
    "MCPClientShim",
    "MCPAuthConfig",
    "FunctionGemmaValidator",
    # Lazy Registration (Phase 0.l)
    "register_example_functions",
    "register_weather_adapter",
    # Skill Library (Phase 1.5)
    "skill_library",
    # Sandbox Execution (Phase 1.8)
    "SandboxEnvironment",
    "ResourceLimits",
    "SandboxSecurityError",
    "SmallModelWorker",
    "ProgrammaticToolExecutor",
    # Runtime Orchestration (Phase 1.10)
    "execute_plan",
    "final_synthesis",
    "run_step",
    "route_request",
    "choose_model",
    "set_available_models",
    # Code Generation (Phase 1.11)
    "StubGenerator",
    "ShardedCatalog",
    "ToolFileSystem",
    # Assessment & Evaluation (Phase 0.a)
    "AgentEvaluator",
    "apply_discount",
    "compute_item_statistics",
    "compute_tax",
    "filter_items_by_category",
    "merge_items",
    "ContextTracker",
    # Control Flow Patterns (Phase 2)
    "ControlFlowPatterns",
    "create_polling_code",
    "create_parallel_code",
    "create_conditional_code",
    "create_retry_code",
    # Mini DSL Executor (Phase 2)
    "MiniDSLExecutor",
    # Planning (Phase 1.9)
    "LargePlanner",
    # Runtime Orchestration (Phase 1.10)
    "execute_plan",
]

# Auto-install secrets redaction on root logger to prevent credential leakage in logs.
install_secrets_redactor()

# ============================================================
# Important: Do not import from orchestrator._internal
# ============================================================
# Users: These are internal implementation details that might change.
# Contributors: Put helper code in _internal, not in public API.
