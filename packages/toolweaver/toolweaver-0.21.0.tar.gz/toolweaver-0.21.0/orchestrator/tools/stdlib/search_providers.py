"""
Web search provider adapters for stdlib web_search tool.

Similar to LiteLLM's multi-provider pattern, this module provides a unified
interface for different web search providers (Tavily, Google, Bing, SerpAPI, etc.).

Users can add custom providers by:
1. Subclassing SearchProvider
2. Implementing the search() method
3. Registering with register_search_provider()

Example custom provider:
    class MySearchProvider(SearchProvider):
        def search(self, query: str, k: int, lang: str) -> list[dict]:
            # Call your API
            response = my_api.search(query, limit=k)
            # Transform to standard format
            return [
                {
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["description"],
                }
                for item in response.results
            ]

    register_search_provider("mysearch", MySearchProvider)
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available search providers
_SEARCH_PROVIDERS: dict[str, type[SearchProvider]] = {}


# ============================================================
# Base Search Provider Interface
# ============================================================


class SearchProvider(ABC):
    """
    Base class for web search providers.

    Subclass this to add support for new search engines.
    """

    @abstractmethod
    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        """
        Execute a web search query.

        Args:
            query: Search query string (already truncated)
            k: Number of results to return (already capped)
            lang: Language code (e.g., "en", "es")

        Returns:
            List of result dictionaries, each containing:
            - title (str): Result title
            - url (str): Result URL
            - snippet (str): Result description/snippet

        Raises:
            Exception: If the search fails (caught by caller)
        """
        pass


# ============================================================
# Stub Provider (for testing/offline mode)
# ============================================================


class StubSearchProvider(SearchProvider):
    """Stub provider that returns fake results for testing."""

    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        logger.debug(f"StubSearchProvider: query={query}, k={k}")
        return [
            {
                "title": f"Result {i+1}",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}&result={i+1}",
                "snippet": f"This is a stub result for '{query}'. Real search requires API configuration.",
            }
            for i in range(k)
        ]


# ============================================================
# Tavily Provider
# ============================================================


class TavilySearchProvider(SearchProvider):
    """
    Tavily search provider.

    Configuration:
        TAVILY_API_KEY: API key from https://tavily.com
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not set in environment")

    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "max_results": k,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:k]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            })

        logger.debug(f"TavilySearchProvider: found {len(results)} results")
        return results


# ============================================================
# Google Custom Search Provider
# ============================================================


class GoogleSearchProvider(SearchProvider):
    """
    Google Custom Search API provider.

    Configuration:
        GOOGLE_SEARCH_API_KEY: API key from Google Cloud Console
        GOOGLE_SEARCH_ENGINE_ID: Custom Search Engine ID (cx parameter)

    Setup:
        1. Create a project at https://console.cloud.google.com
        2. Enable Custom Search API
        3. Create API key
        4. Create Custom Search Engine at https://programmablesearchengine.google.com
        5. Get the Search Engine ID (cx)
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

        if not self.api_key:
            raise ValueError("GOOGLE_SEARCH_API_KEY not set in environment")
        if not self.engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID not set in environment")

    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.api_key,
                "cx": self.engine_id,
                "q": query,
                "num": min(k, 10),  # Google API max is 10 per request
                "lr": f"lang_{lang}",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", [])[:k]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })

        logger.debug(f"GoogleSearchProvider: found {len(results)} results")
        return results


# ============================================================
# SerpAPI Provider (supports Google, Bing, DuckDuckGo, etc.)
# ============================================================


class SerpAPISearchProvider(SearchProvider):
    """
    SerpAPI provider - unified API for Google, Bing, DuckDuckGo, and more.

    Configuration:
        SERPAPI_API_KEY: API key from https://serpapi.com
        SERPAPI_ENGINE: Search engine to use (default: "google")
                        Options: google, bing, duckduckgo, yahoo, yandex, baidu

    SerpAPI is a paid service that provides a unified interface to multiple
    search engines without needing separate API keys for each.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.engine = os.getenv("SERPAPI_ENGINE", "google")

        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY not set in environment")

    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY not set in environment")

        params: dict[str, str | int] = {
            "api_key": self.api_key,
            "engine": self.engine,
            "q": query,
            "num": k,
            "hl": lang,
        }
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        # SerpAPI uses different key names depending on engine
        organic_results = data.get("organic_results", [])

        for item in organic_results[:k]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })

        logger.debug(f"SerpAPISearchProvider ({self.engine}): found {len(results)} results")
        return results


# ============================================================
# Bing Search Provider
# ============================================================


class BingSearchProvider(SearchProvider):
    """
    Microsoft Bing Search API provider.

    Configuration:
        BING_SEARCH_API_KEY: API key from Azure portal
        BING_SEARCH_ENDPOINT: Custom endpoint (default: global endpoint)

    Setup:
        1. Create Bing Search resource in Azure portal
        2. Get API key from Keys and Endpoint section
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("BING_SEARCH_API_KEY")
        self.endpoint = os.getenv(
            "BING_SEARCH_ENDPOINT",
            "https://api.bing.microsoft.com/v7.0/search"
        )

        if not self.api_key:
            raise ValueError("BING_SEARCH_API_KEY not set in environment")

    def search(self, query: str, k: int, lang: str) -> list[dict[str, Any]]:
        response = requests.get(
            self.endpoint,
            params={  # type: ignore[arg-type]
                "q": query,
                "count": k,
                "mkt": f"{lang}-{lang.upper()}",  # e.g., en-US
            },
            headers={
                "Ocp-Apim-Subscription-Key": self.api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("webPages", {}).get("value", [])[:k]:
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            })

        logger.debug(f"BingSearchProvider: found {len(results)} results")
        return results


# ============================================================
# Provider Registry
# ============================================================


def register_search_provider(name: str, provider_class: type[SearchProvider]) -> None:
    """
    Register a custom search provider.

    Args:
        name: Provider name (e.g., "mysearch", "custom")
        provider_class: SearchProvider subclass

    Example:
        class MyProvider(SearchProvider):
            def search(self, query, k, lang):
                # Your implementation
                return [...]

        register_search_provider("myprovider", MyProvider)
    """
    if not issubclass(provider_class, SearchProvider):
        raise TypeError(f"{provider_class} must subclass SearchProvider")

    _SEARCH_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered search provider: {name}")


def get_search_provider(name: str) -> SearchProvider | ProviderRouter[SearchProvider]:
    """
    Get a search provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "tavily,brave,stub")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (none, tavily, google, serpapi, bing) or comma-separated list

    Returns:
        SearchProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or configuration missing

    Examples:
        # Single provider
        provider = get_search_provider("tavily")

        # Automatic fallback chain
        provider = get_search_provider("tavily,google,stub")
        # Tries tavily first, falls back to google, then stub
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for search: {provider_names}")
        return ProviderRouter(
            provider_getter=get_search_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    if name == "none" or name == "stub":
        return StubSearchProvider()

    if name not in _SEARCH_PROVIDERS:
        available = ", ".join(["none", "stub"] + list(_SEARCH_PROVIDERS.keys()))
        raise ValueError(
            f"Search provider '{name}' not found. "
            f"Available providers: {available}"
        )

    provider_class = _SEARCH_PROVIDERS[name]

    try:
        return provider_class()
    except ValueError as e:
        # Re-raise configuration errors with provider context
        raise ValueError(f"Failed to initialize {name} provider: {e}") from e


# ============================================================
# Auto-register built-in providers
# ============================================================

register_search_provider("tavily", TavilySearchProvider)
register_search_provider("google", GoogleSearchProvider)
register_search_provider("serpapi", SerpAPISearchProvider)
register_search_provider("bing", BingSearchProvider)
