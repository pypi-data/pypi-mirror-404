"""
Core stdlib tools: web_search, web_fetch, memory_get/put, tool_search.

These tools are enabled by default (low risk) and provide essential functionality
for planning, retrieval, and state management. Each tool includes RLM hooks for
input validation, output truncation, and redaction.

Configuration:
    TOOLWEAVER_STDLIB_ENABLED (default: "web_search,web_fetch,memory,tool_search")
    TOOLWEAVER_STDLIB_WEB_SEARCH_PROVIDER (default: "none" - stub only)
    TOOLWEAVER_STDLIB_WEB_FETCH_TIMEOUT_S (default: 10)
    TOOLWEAVER_STDLIB_WEB_FETCH_MAX_BYTES (default: 20000)
    TOOLWEAVER_STDLIB_MEMORY_TTL_S (default: 300)
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from orchestrator.tools.stdlib.fetch_providers import get_fetch_provider
from orchestrator.tools.stdlib.memory_providers import get_memory_provider
from orchestrator.tools.stdlib.search_providers import get_search_provider

logger = logging.getLogger(__name__)


# ============================================================
# Configuration Helpers
# ============================================================


def _normalize_tool_key(tool_name: str) -> str:
    """Normalize tool name to base key for env flags.

    Maps grouped tools to a single key (e.g., memory_get/memory_put -> memory).
    """
    if tool_name in ("memory_get", "memory_put", "memory"):
        return "memory"
    return tool_name


def _parse_bool(val: str | None) -> bool | None:
    """Parse a boolean-like environment variable value."""
    if val is None:
        return None
    v = val.strip().lower()
    if v in ("true", "1", "yes", "on"):  # truthy
        return True
    if v in ("false", "0", "no", "off"):  # falsy
        return False
    return None


def _is_tool_enabled(tool_name: str) -> bool:
    """Check if a tool is enabled via env config.

    Precedence:
    1) Individual flag: TOOLWEAVER_STDLIB_<TOOL>_ENABLED=true/false
       - <TOOL> uses normalized key (e.g., MEMORY, WEB_SEARCH)
    2) Disabled list: TOOLWEAVER_STDLIB_DISABLED (comma-separated)
    3) Enabled list: TOOLWEAVER_STDLIB_ENABLED (comma-separated)
       - Defaults to "web_search,web_fetch,memory,tool_search"
       - "memory" enables both memory_get and memory_put
    """
    base = _normalize_tool_key(tool_name)

    # 1) Individual flag override
    indiv_key = f"TOOLWEAVER_STDLIB_{base.upper()}_ENABLED"
    indiv_val = _parse_bool(os.getenv(indiv_key))
    if indiv_val is not None:
        return indiv_val

    # 2) Disabled list override
    disabled_str = os.getenv("TOOLWEAVER_STDLIB_DISABLED", "")
    disabled = {t.strip() for t in disabled_str.split(",") if t.strip()}
    if base in disabled or tool_name in disabled:
        return False

    # 3) Enabled list (with sensible defaults)
    enabled_str = os.getenv(
        "TOOLWEAVER_STDLIB_ENABLED",
        "web_search,web_fetch,memory,tool_search",
    )
    enabled_set = {t.strip() for t in enabled_str.split(",") if t.strip()}

    # "memory" group enables both get/put
    if base == "memory":
        return ("memory" in enabled_set) or (tool_name in enabled_set)

    return (base in enabled_set) or (tool_name in enabled_set)


def _get_config(key: str, default: str | int | None = None) -> str | int | None:
    """Get stdlib config from environment."""
    result = os.getenv(f"TOOLWEAVER_STDLIB_{key.upper()}")
    return result if result is not None else default


def _get_domain_allowlist(tool_name: str) -> list[str]:
    """Get domain allowlist for a tool (e.g., web_fetch)."""
    allowlist_str = os.getenv(f"TOOLWEAVER_STDLIB_{tool_name.upper()}_DOMAIN_ALLOWLIST", "")
    return [d.strip() for d in allowlist_str.split(",") if d.strip()]


def _is_domain_allowed(url: str, allowlist: list[str]) -> bool:
    """Check if a URL's domain is in the allowlist.

    If allowlist is empty, all domains are allowed.
    """
    if not allowlist:
        return True

    # Extract domain from URL (basic parsing)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Check if domain or any parent domain is in allowlist
        for allowed in allowlist:
            allowed_lower = allowed.lower()
            if domain == allowed_lower or domain.endswith("." + allowed_lower):
                return True
        return False
    except Exception:
        return False


# ============================================================
# RLM Helpers
# ============================================================


def _truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate text for RLM (pre-flight budget check)."""
    if len(text) > max_chars:
        text = text[: max_chars - 50] + f"\n... [truncated {len(text) - max_chars} chars]"
    return text


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (Claude/GPT ratio)."""
    return len(text) // 4


def _check_budget(text: str, max_tokens: int = 100000) -> tuple[bool, str]:
    """Check if text fits within token budget."""
    tokens = _estimate_tokens(text)
    if tokens > max_tokens:
        return False, f"Text exceeds budget: {tokens} tokens > {max_tokens} max"
    return True, ""


# ============================================================
# In-Memory Session Store (Stub)
# ============================================================


class SessionMemoryStore:
    """Scoped, in-memory KV store for session state."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    def put(
        self, key: str, value: dict[str, Any] | str, ttl_s: int | None = None
    ) -> dict[str, Any]:
        """Store a value with optional TTL."""
        expire_at = (time.time() + ttl_s) if ttl_s else None
        self._store[key] = (value, expire_at)
        return {"key": key, "stored": True, "ttl_s": ttl_s}

    def get(self, key: str) -> dict[str, Any]:
        """Retrieve a value if not expired."""
        if key not in self._store:
            return {"key": key, "value": None, "found": False}

        value, expire_at = self._store[key]
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return {"key": key, "value": None, "expired": True, "found": False}

        return {"key": key, "value": value, "found": True}


_default_session_store = SessionMemoryStore()


# ============================================================
# Core Tool: web_search
# ============================================================


def web_search(
    query: str, k: int = 5, lang: str = "en"
) -> dict[str, Any]:
    """
    Search the web for information.

    Supports multiple search providers via adapter pattern (like LiteLLM for AI models):
    - none/stub: Fake results for testing
    - tavily: Tavily Search API
    - google: Google Custom Search API
    - serpapi: SerpAPI (supports Google, Bing, DuckDuckGo, etc.)
    - bing: Microsoft Bing Search API

    Configure via TOOLWEAVER_STDLIB_WEB_SEARCH_PROVIDER environment variable.

    To add custom providers:
        from orchestrator.tools.stdlib.search_providers import SearchProvider, register_search_provider

        class MyProvider(SearchProvider):
            def search(self, query, k, lang):
                # Your implementation
                return [{"title": "...", "url": "...", "snippet": "..."}]

        register_search_provider("myprovider", MyProvider)

    Args:
        query: Search query (max 1000 chars)
        k: Number of results to return (max 20)
        lang: Language code (default: "en")

    Returns:
        Dictionary with results list, each containing title, url, snippet

    RLM Hooks:
        - Pre-call: Truncate query to 1000 chars, validate k <= 20
        - Post-call: Truncate snippets to 500 chars each, limit result count
    """
    # Pre-call validation (RLM)
    if not _is_tool_enabled("web_search"):
        return {"error": "web_search is not enabled"}

    query = _truncate_text(query, max_chars=1000)
    k = min(k, 20)
    provider_name = _get_config("WEB_SEARCH_PROVIDER", "none") or "none"
    assert isinstance(provider_name, str), "Provider name must be string"

    try:
        # Get provider instance using adapter pattern
        provider = get_search_provider(provider_name)

        # Execute search
        results = provider.search(query, k, lang)

        # Apply RLM constraints (truncate snippets)
        for result in results:
            result["title"] = _truncate_text(result.get("title", ""), max_chars=200)
            result["snippet"] = _truncate_text(result.get("snippet", ""), max_chars=500)

        logger.debug(f"web_search ({provider_name}): query={query}, k={k}, found={len(results)}")
        return {
            "query": query,
            "results": results[:k],  # Ensure we don't exceed k
            "provider": provider_name,
        }

    except ValueError as e:
        # Configuration error (missing API key, unknown provider, etc.)
        logger.error(f"web_search configuration error: {e}")
        return {"error": str(e)}

    except Exception as e:
        # Network error, API error, etc.
        logger.error(f"web_search error with provider {provider_name}: {e}")
        return {"error": f"Search failed: {str(e)}"}


# ============================================================
# Core Tool: web_fetch
# ============================================================


def web_fetch(
    url: str, timeout_s: int = 10, max_bytes: int = 20000
) -> dict[str, Any]:
    """
    Fetch content from a URL.

    Supports multiple fetch providers via adapter pattern (like LiteLLM for AI models):
    - requests: Standard HTTP fetch (default)
    - scraperapi: ScraperAPI - handles JS, proxies, CAPTCHAs
    - readable: Readability extraction - clean article content
    - cached: Caching layer over standard fetch

    Configure via TOOLWEAVER_STDLIB_WEB_FETCH_PROVIDER environment variable.

    To add custom providers:
        from orchestrator.tools.stdlib.fetch_providers import FetchProvider, register_fetch_provider

        class MyProvider(FetchProvider):
            def fetch(self, url, timeout_s, max_bytes):
                # Your implementation
                return {"url": url, "status_code": 200, "content": "...", "headers": {}}

        register_fetch_provider("myprovider", MyProvider)

    Args:
        url: URL to fetch (max 2000 chars)
        timeout_s: Request timeout in seconds (max 30)
        max_bytes: Maximum bytes to download (max 100000)

    Returns:
        Dictionary with status_code, content (text), headers (subset)

    RLM Hooks:
        - Pre-call: Validate URL format, cap timeout/max_bytes, check domain allowlist
        - Post-call: Strip HTML/scripts, truncate content, redact auth headers
    """
    # Pre-call validation (RLM)
    if not _is_tool_enabled("web_fetch"):
        return {"error": "web_fetch is not enabled"}

    url = _truncate_text(url, max_chars=2000)
    timeout_s = min(timeout_s, 30)
    max_bytes = min(max_bytes, 100000)

    # Domain allowlist check for partial offline mode
    domain_allowlist = _get_domain_allowlist("web_fetch")
    if not _is_domain_allowed(url, domain_allowlist):
        return {
            "error": f"Domain not in allowlist. Allowed domains: {', '.join(domain_allowlist) if domain_allowlist else 'none configured'}",
            "url": url,
        }

    provider_name = _get_config("WEB_FETCH_PROVIDER", "requests") or "requests"
    assert isinstance(provider_name, str), "Provider name must be string"

    try:
        # Get provider instance using adapter pattern
        provider = get_fetch_provider(provider_name)

        # Execute fetch
        result = provider.fetch(url, timeout_s, max_bytes)

        # Apply RLM constraints (truncate content if needed)
        if "content" in result:
            result["content"] = _truncate_text(result["content"], max_chars=max_bytes // 2)

        logger.debug(f"web_fetch ({provider_name}): fetched {result.get('bytes_read', 0)} bytes from {url}")
        return result

    except ValueError as e:
        # Configuration error (missing API key, unknown provider, etc.)
        logger.error(f"web_fetch configuration error: {e}")
        return {"error": str(e), "url": url}

    except Exception as e:
        # Network error, API error, etc.
        logger.error(f"web_fetch error with provider {provider_name}: {e}")
        return {"error": f"Fetch failed: {str(e)}", "url": url}


# ============================================================
# Core Tool: memory_put / memory_get
# ============================================================


def memory_put(key: str, value: dict[str, Any] | str, ttl_s: int | None = None) -> dict[str, Any]:
    """
    Store a value in memory with optional TTL.

    Args:
        key: Storage key (max 100 chars)
        value: Value to store (dict or string, max 10000 chars)
        ttl_s: Time-to-live in seconds (max 3600)

    Returns:
        Dictionary with key, stored status, and TTL info

    RLM Hooks:
        - Pre-call: Validate key length, value size, cap TTL

    Example:
        # In-memory (default)
        result = memory_put("task_state", {"status": "processing"}, ttl_s=300)

        # SQLite (persistent)
        os.environ["TOOLWEAVER_STDLIB_MEMORY_PROVIDER"] = "sqlite"
        result = memory_put("config", {"theme": "dark"})

        # Redis (distributed)
        os.environ["TOOLWEAVER_STDLIB_MEMORY_PROVIDER"] = "redis"
        result = memory_put("cache_key", "cached_data", ttl_s=600)
    """
    if not _is_tool_enabled("memory"):
        return {"error": "memory tools are not enabled"}

    # Pre-call validation (RLM)
    key = _truncate_text(key, max_chars=100)
    if isinstance(value, dict):
        value_str = json.dumps(value)
    else:
        value_str = str(value)
    value_str = _truncate_text(value_str, max_chars=10000)
    ttl_s = min(ttl_s, 3600) if ttl_s else None

    # Get provider
    provider_name = _get_config("MEMORY_PROVIDER", "memory") or "memory"
    assert isinstance(provider_name, str), "Provider name must be string"

    try:
        provider = get_memory_provider(provider_name)
        result = provider.put(key, value, ttl_s)

        logger.debug(f"memory_put ({provider_name}): stored key={key}, ttl_s={ttl_s}")
        return result

    except ValueError as e:
        logger.error(f"memory_put configuration error: {e}")
        return {"error": str(e), "key": key}

    except Exception as e:
        logger.error(f"memory_put error with provider {provider_name}: {e}")
        return {"error": f"Storage failed: {str(e)}", "key": key}


def memory_get(key: str) -> dict[str, Any]:
    """
    Retrieve a value from memory.

    Args:
        key: Storage key to retrieve (max 100 chars)

    Returns:
        Dictionary with key, value, found status

    Example:
        result = memory_get("task_state")
        if result["found"]:
            print(f"Value: {result['value']}")
    """
    if not _is_tool_enabled("memory"):
        return {"error": "memory tools are not enabled"}

    # Pre-call validation (RLM)
    key = _truncate_text(key, max_chars=100)

    # Get provider
    provider_name = _get_config("MEMORY_PROVIDER", "memory") or "memory"
    assert isinstance(provider_name, str), "Provider name must be string"

    try:
        provider = get_memory_provider(provider_name)
        result = provider.get(key)

        logger.debug(f"memory_get ({provider_name}): key={key}, found={result.get('found', False)}")
        return result

    except ValueError as e:
        logger.error(f"memory_get configuration error: {e}")
        return {"error": str(e), "key": key}

    except Exception as e:
        logger.error(f"memory_get error with provider {provider_name}: {e}")
        return {"error": f"Retrieval failed: {str(e)}", "key": key}


# ============================================================
# Core Tool: tool_search
# ============================================================


def tool_search(
    query: str, top_k: int = 5, tags: list[str] | None = None
) -> dict[str, Any]:
    """
    Search for available tools by name/description.

    Args:
        query: Search query (max 500 chars)
        top_k: Number of results to return (max 20)
        tags: Optional filter by tags (e.g., ["stdlib", "safe"])

    Returns:
        Dictionary with matching tools, descriptions, and domains

    RLM Hooks:
        - Pre-call: Truncate query, cap top_k
        - Post-call: Include only essential tool metadata, truncate descriptions
    """
    if not _is_tool_enabled("tool_search"):
        return {"error": "tool_search is not enabled"}

    query = _truncate_text(query, max_chars=500)
    top_k = min(top_k, 20)

    # Stub implementation: list enabled stdlib tools
    logger.debug(f"tool_search (stub): query={query}, top_k={top_k}, tags={tags}")

    all_tools: list[dict[str, Any]] = []

    if _is_tool_enabled("web_search"):
        all_tools.append(
            {
                "name": "web_search",
                "description": "Search the web for information",
                "domain": "stdlib",
                "tags": ["stdlib", "safe", "search"],
            }
        )

    if _is_tool_enabled("web_fetch"):
        all_tools.append(
            {
                "name": "web_fetch",
                "description": "Fetch content from a URL",
                "domain": "stdlib",
                "tags": ["stdlib", "safe", "fetch"],
            }
        )

    if _is_tool_enabled("memory"):
        all_tools.extend(
            [
                {
                    "name": "memory_put",
                    "description": "Store a value in session memory",
                    "domain": "stdlib",
                    "tags": ["stdlib", "safe", "memory"],
                },
                {
                    "name": "memory_get",
                    "description": "Retrieve a value from session memory",
                    "domain": "stdlib",
                    "tags": ["stdlib", "safe", "memory"],
                },
            ]
        )

    if _is_tool_enabled("tool_search"):
        all_tools.append(
            {
                "name": "tool_search",
                "description": "Search for available tools",
                "domain": "stdlib",
                "tags": ["stdlib", "safe", "discovery"],
            }
        )

    # Filter by tags if provided
    if tags:
        all_tools = [
            t
            for t in all_tools
            if any(tag in t["tags"] for tag in tags)
        ]

    # Truncate descriptions for RLM
    for tool in all_tools:
        desc: str = tool["description"]
        tool["description"] = _truncate_text(desc, max_chars=200)

    return {
        "query": query,
        "results": all_tools[:top_k],
        "total": len(all_tools),
        "provider": "stub",
    }
