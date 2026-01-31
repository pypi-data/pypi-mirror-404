"""
Web fetch provider adapters for stdlib web_fetch tool.

Similar to search_providers, this module provides a unified interface for
different HTTP fetching backends (requests, httpx, playwright, etc.).

Users can add custom providers by:
1. Subclassing FetchProvider
2. Implementing the fetch() method
3. Registering with register_fetch_provider()

Example custom provider:
    class ScraperAPIProvider(FetchProvider):
        def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict:
            # Use ScraperAPI proxy
            response = requests.get(
                "https://api.scraperapi.com/",
                params={"api_key": self.api_key, "url": url},
                timeout=timeout_s,
            )
            return {
                "url": url,
                "status_code": response.status_code,
                "content": response.text[:max_bytes],
                "headers": dict(response.headers),
            }

    register_fetch_provider("scraperapi", ScraperAPIProvider)
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

# Registry of available fetch providers
_FETCH_PROVIDERS: dict[str, type[FetchProvider]] = {}


# ============================================================
# Base Fetch Provider Interface
# ============================================================


class FetchProvider(ABC):
    """
    Base class for web fetch providers.

    Subclass this to add support for different HTTP backends or scrapers.
    """

    @abstractmethod
    def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict[str, Any]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch (already validated)
            timeout_s: Timeout in seconds (already capped)
            max_bytes: Maximum bytes to read (already capped)

        Returns:
            Dictionary containing:
            - url (str): The fetched URL
            - status_code (int): HTTP status code
            - content (str): Content text
            - headers (dict): Response headers (safe subset)
            - bytes_read (int, optional): Actual bytes read
            - truncated (bool, optional): Whether content was truncated

        Raises:
            Exception: If the fetch fails (caught by caller)
        """
        pass


# ============================================================
# Requests Provider (Default)
# ============================================================


class RequestsFetchProvider(FetchProvider):
    """Standard HTTP fetch using requests library."""

    def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict[str, Any]:
        response = requests.get(
            url,
            timeout=timeout_s,
            stream=True,
            headers={"User-Agent": "ToolWeaver/1.0"},
        )
        response.raise_for_status()

        # Read content up to max_bytes
        content_chunks = []
        bytes_read = 0

        for chunk in response.iter_content(chunk_size=8192):
            if bytes_read + len(chunk) > max_bytes:
                # Read only what fits in the limit
                remaining = max_bytes - bytes_read
                content_chunks.append(chunk[:remaining])
                bytes_read = max_bytes
                break
            content_chunks.append(chunk)
            bytes_read += len(chunk)

        content_bytes = b"".join(content_chunks)

        # Try to decode as text
        try:
            content_text = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content_text = str(content_bytes)

        # Return safe subset of headers (no auth tokens)
        safe_headers = {}
        for key in ["content-type", "content-length", "last-modified"]:
            if key in response.headers:
                safe_headers[key] = response.headers[key]

        logger.debug(f"RequestsFetchProvider: fetched {bytes_read} bytes from {url}")

        return {
            "url": url,
            "status_code": response.status_code,
            "content": content_text,
            "headers": safe_headers,
            "bytes_read": bytes_read,
            "truncated": bytes_read >= max_bytes,
        }


# ============================================================
# ScraperAPI Provider (for hard-to-scrape sites)
# ============================================================


class ScraperAPIFetchProvider(FetchProvider):
    """
    ScraperAPI provider - handles JS rendering, proxies, CAPTCHAs.

    Configuration:
        SCRAPERAPI_API_KEY: API key from https://scraperapi.com

    ScraperAPI is useful for:
    - Sites that require JavaScript rendering
    - Sites that block bots
    - Sites with CAPTCHAs
    - Geographic restrictions
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("SCRAPERAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SCRAPERAPI_API_KEY not set in environment")

    def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict[str, Any]:
        response = requests.get(
            "https://api.scraperapi.com/",
            params={
                "api_key": self.api_key,
                "url": url,
                "render": "false",  # Set to "true" for JS rendering
            },
            timeout=timeout_s,
            stream=True,
        )
        response.raise_for_status()

        # Read content up to max_bytes
        content = response.text[:max_bytes]
        bytes_read = len(content.encode("utf-8"))

        logger.debug(f"ScraperAPIFetchProvider: fetched {bytes_read} bytes from {url}")

        return {
            "url": url,
            "status_code": response.status_code,
            "content": content,
            "headers": {"content-type": response.headers.get("content-type", "")},
            "bytes_read": bytes_read,
            "truncated": len(response.text) > max_bytes,
        }


# ============================================================
# ReadableWeb Provider (cleaned content extraction)
# ============================================================


class ReadableWebProvider(FetchProvider):
    """
    Fetch and extract main content using readability-style parsing.

    Requires: beautifulsoup4, readability-lxml

    This provider:
    - Strips ads, navigation, footers
    - Extracts main article content
    - Returns clean, readable text
    """

    def __init__(self) -> None:
        try:
            from readability import Document
            self.Document = Document
        except ImportError as e:
            raise ValueError(
                "readability-lxml not installed. "
                "Install with: pip install readability-lxml"
            ) from e

    def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict[str, Any]:
        # Fetch raw HTML
        response = requests.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": "ToolWeaver/1.0"},
        )
        response.raise_for_status()

        # Extract main content
        doc = self.Document(response.text)
        title = doc.title()
        content_html = doc.summary()

        # Convert HTML to text (basic)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content_html, "html.parser")
        content_text = soup.get_text(separator="\n", strip=True)

        # Truncate to max_bytes
        content_text = content_text[:max_bytes]
        bytes_read = len(content_text.encode("utf-8"))

        logger.debug(f"ReadableWebProvider: extracted {bytes_read} bytes from {url}")

        result: dict[str, Any] = {
            "url": url,
            "status_code": response.status_code,
            "content": content_text,
            "headers": {"content-type": "text/plain"},
            "title": title,
            "bytes_read": bytes_read,
            "truncated": False,
        }
        return result


# ============================================================
# Cache Provider (with disk/redis caching)
# ============================================================


class CachedFetchProvider(FetchProvider):
    """
    Fetch provider with caching layer.

    Uses underlying provider (default: requests) but caches responses.
    Useful for repeated fetches of the same URLs.

    Configuration:
        FETCH_CACHE_BACKEND: "memory", "disk", or "redis" (default: memory)
        FETCH_CACHE_TTL: Cache TTL in seconds (default: 3600)
    """

    def __init__(self) -> None:
        self.cache: dict[str, dict[str, Any]] = {}  # Simple in-memory cache
        self.cache_ttl = int(os.getenv("FETCH_CACHE_TTL", "3600"))
        self.underlying = RequestsFetchProvider()

    def fetch(self, url: str, timeout_s: int, max_bytes: int) -> dict[str, Any]:
        import time

        cache_key = f"{url}:{max_bytes}"

        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                logger.debug(f"CachedFetchProvider: cache hit for {url}")
                return cached["result"]  # type: ignore[no-any-return]

        # Fetch from underlying provider
        result = self.underlying.fetch(url, timeout_s, max_bytes)

        # Cache result
        self.cache[cache_key] = {
            "result": result,
            "timestamp": time.time(),
        }

        logger.debug(f"CachedFetchProvider: cached result for {url}")
        return result


# ============================================================
# Provider Registry
# ============================================================


def register_fetch_provider(name: str, provider_class: type[FetchProvider]) -> None:
    """
    Register a custom fetch provider.

    Args:
        name: Provider name (e.g., "scraperapi", "cached")
        provider_class: FetchProvider subclass

    Example:
        class MyProvider(FetchProvider):
            def fetch(self, url, timeout_s, max_bytes):
                # Your implementation
                return {...}

        register_fetch_provider("myprovider", MyProvider)
    """
    if not issubclass(provider_class, FetchProvider):
        raise TypeError(f"{provider_class} must subclass FetchProvider")

    _FETCH_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered fetch provider: {name}")


def get_fetch_provider(name: str) -> FetchProvider | ProviderRouter[FetchProvider]:
    """
    Get a fetch provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "scraperapi,requests")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (requests, scraperapi, readable, cached) or comma-separated list

    Returns:
        FetchProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or configuration missing

    Examples:
        # Single provider
        provider = get_fetch_provider("requests")

        # Automatic fallback chain
        provider = get_fetch_provider("scraperapi,readable,requests")
        # Tries scraperapi first, falls back to readable, then requests
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for fetch: {provider_names}")
        return ProviderRouter(
            provider_getter=get_fetch_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    if name == "requests" or name == "default":
        return RequestsFetchProvider()

    if name not in _FETCH_PROVIDERS:
        available = ", ".join(["requests", "default"] + list(_FETCH_PROVIDERS.keys()))
        raise ValueError(
            f"Fetch provider '{name}' not found. "
            f"Available providers: {available}"
        )

    provider_class = _FETCH_PROVIDERS[name]

    try:
        return provider_class()
    except ValueError as e:
        # Re-raise configuration errors with provider context
        raise ValueError(f"Failed to initialize {name} provider: {e}") from e


# ============================================================
# Auto-register built-in providers
# ============================================================

register_fetch_provider("scraperapi", ScraperAPIFetchProvider)
register_fetch_provider("readable", ReadableWebProvider)
register_fetch_provider("cached", CachedFetchProvider)
