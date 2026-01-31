"""
Tool search provider adapters for stdlib tool_search tool.

This module provides a unified interface for different tool discovery backends
(local registry, vector DB, remote catalog, etc.).

Users can add custom providers by:
1. Subclassing ToolSearchProvider
2. Implementing the search() method
3. Registering with register_tool_search_provider()

Example custom provider:
    class VectorDBProvider(ToolSearchProvider):
        def __init__(self) -> None:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(url=os.getenv("QDRANT_URL"))

        def search(self, query: str, top_k: int, tags: list[str] | None) -> list[dict]:
            # Vector search for tools
            results = self.client.search(
                collection_name="tools",
                query_vector=self._embed(query),
                limit=top_k,
            )
            return [self._format_tool(r) for r in results]

    register_tool_search_provider("vectordb", VectorDBProvider)
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available tool search providers
_TOOL_SEARCH_PROVIDERS: dict[str, type[ToolSearchProvider]] = {}


# ============================================================
# Base Tool Search Provider Interface
# ============================================================


class ToolSearchProvider(ABC):
    """
    Base class for tool search providers.

    Subclass this to add support for different discovery backends
    (vector DB, remote catalog, enterprise tool registry, etc.).
    """

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int,
        tags: list[str] | None,
        registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Search for tools matching the query.

        Args:
            query: Search query (already validated/truncated)
            top_k: Maximum results to return (already capped)
            tags: Optional tag filters (already validated)
            registry: Current tool registry (for reference)

        Returns:
            List of tool dictionaries, each containing:
            - name (str): Tool name
            - description (str): Tool description
            - tags (list[str], optional): Tool tags
            - score (float, optional): Relevance score (0-1)

        Raises:
            Exception: If search fails (caught by caller)
        """
        pass


# ============================================================
# Local Registry Provider (Default)
# ============================================================


class LocalRegistryProvider(ToolSearchProvider):
    """
    Simple keyword-based search over local tool registry.

    Scores tools by keyword matches in name/description.
    No external dependencies required.
    """

    def search(
        self,
        query: str,
        top_k: int,
        tags: list[str] | None,
        registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for name, tool_info in registry.items():
            # Filter by tags if specified
            if tags:
                tool_tags = tool_info.get("tags", [])
                if not any(tag in tool_tags for tag in tags):
                    continue

            # Score by keyword matches
            desc_lower = tool_info.get("description", "").lower()
            name_lower = name.lower()

            # Count matches in name (weighted 2x) and description
            name_matches = sum(1 for word in query_words if word in name_lower)
            desc_matches = sum(1 for word in query_words if word in desc_lower)
            score = (name_matches * 2 + desc_matches) / max(len(query_words), 1)

            if score > 0:
                results.append({
                    "name": name,
                    "description": tool_info.get("description", ""),
                    "tags": tool_info.get("tags", []),
                    "score": min(score, 1.0),
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        # Return top_k results
        return results[:top_k]


# ============================================================
# Vector DB Provider (Qdrant)
# ============================================================


class VectorDBProvider(ToolSearchProvider):
    """
    Vector similarity search using Qdrant.

    Embeds tool descriptions and performs semantic search.
    Requires: pip install qdrant-client sentence-transformers
    Configure with: QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
    """

    def __init__(self) -> None:
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ValueError(
                "VectorDBProvider requires 'qdrant-client' and 'sentence-transformers'. "
                "Install with: pip install qdrant-client sentence-transformers"
            ) from e

        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.collection = os.getenv("QDRANT_COLLECTION", "toolweaver_tools")
        self.encoder = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    def search(
        self,
        query: str,
        top_k: int,
        tags: list[str] | None,
        registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Embed query
        query_vector = self.encoder.encode(query).tolist()

        # Build filter for tags if specified
        search_filter = None
        if tags:
            from qdrant_client.models import FieldCondition, Filter, MatchAny
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="tags",
                        match=MatchAny(any=tags),
                    )
                ]
            )

        # Perform vector search
        search_results = cast(Any, self.client).search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=search_filter,
        )

        # Format results
        results = []
        for hit in search_results:
            results.append({
                "name": hit.payload.get("name", ""),
                "description": hit.payload.get("description", ""),
                "tags": hit.payload.get("tags", []),
                "score": hit.score,
            })

        return results


# ============================================================
# Remote Catalog Provider
# ============================================================


class RemoteCatalogProvider(ToolSearchProvider):
    """
    Search tools from a remote HTTP catalog/API.

    Useful for enterprise tool registries or marketplace integrations.
    Configure with: TOOL_CATALOG_URL, TOOL_CATALOG_API_KEY
    """

    def __init__(self) -> None:
        import requests

        self.catalog_url = os.getenv("TOOL_CATALOG_URL")
        if not self.catalog_url:
            raise ValueError(
                "RemoteCatalogProvider requires TOOL_CATALOG_URL environment variable. "
                "Example: https://tools.example.com/api/search"
            )

        self.api_key = os.getenv("TOOL_CATALOG_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def search(
        self,
        query: str,
        top_k: int,
        tags: list[str] | None,
        registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Query remote catalog
        if not self.catalog_url:
            return []

        params: dict[str, str | int] = {
            "q": query,
            "limit": top_k,
        }
        if tags:
            params["tags"] = ",".join(tags)

        response = self.session.get(self.catalog_url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        # Expected format: {"tools": [{"name": "...", "description": "...", "tags": [...]}]}
        tools = data.get("tools", [])

        # Normalize results
        results = []
        for tool in tools[:top_k]:
            results.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "tags": tool.get("tags", []),
                "score": tool.get("score", 0.5),
            })

        return results


# ============================================================
# Hybrid Provider (Local + Vector)
# ============================================================


class HybridProvider(ToolSearchProvider):
    """
    Combines local registry search with vector search for better results.

    Merges results from both LocalRegistry and VectorDB providers.
    Requires: Vector DB provider dependencies
    Configure with: HYBRID_VECTOR_WEIGHT (default: 0.5)
    """

    def __init__(self) -> None:
        self.local_provider = LocalRegistryProvider()
        self.vector_provider = VectorDBProvider()
        self.vector_weight = float(os.getenv("HYBRID_VECTOR_WEIGHT", "0.5"))

    def search(
        self,
        query: str,
        top_k: int,
        tags: list[str] | None,
        registry: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # Get results from both providers
        local_results = self.local_provider.search(query, top_k * 2, tags, registry)
        vector_results = self.vector_provider.search(query, top_k * 2, tags, registry)

        # Merge and re-rank
        combined: dict[str, dict[str, Any]] = {}

        for result in local_results:
            name = result["name"]
            combined[name] = result.copy()
            combined[name]["local_score"] = result["score"]
            combined[name]["vector_score"] = 0.0

        for result in vector_results:
            name = result["name"]
            if name in combined:
                combined[name]["vector_score"] = result["score"]
            else:
                combined[name] = result.copy()
                combined[name]["local_score"] = 0.0
                combined[name]["vector_score"] = result["score"]

        # Calculate hybrid score
        for _name, data in combined.items():
            local_score = data.get("local_score", 0.0)
            vector_score = data.get("vector_score", 0.0)
            data["score"] = (
                (1 - self.vector_weight) * local_score
                + self.vector_weight * vector_score
            )

        # Sort by hybrid score and return top_k
        results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# ============================================================
# Provider Registry
# ============================================================


def register_tool_search_provider(name: str, provider_class: type[ToolSearchProvider]) -> None:
    """
    Register a custom tool search provider.

    Args:
        name: Provider name (e.g., "vectordb", "remote", "custom")
        provider_class: Provider class (subclass of ToolSearchProvider)

    Example:
        register_tool_search_provider("vectordb", VectorDBProvider)
    """
    _TOOL_SEARCH_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered tool search provider: {name}")


def get_tool_search_provider(name: str) -> ToolSearchProvider | ProviderRouter[ToolSearchProvider]:
    """
    Get a tool search provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "vectordb,local")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (e.g., "local", "vectordb", "remote", "hybrid") or comma-separated list

    Returns:
        ToolSearchProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or instantiation fails

    Examples:
        # Single provider
        provider = get_tool_search_provider("vectordb")
        results = provider.search("file operations", top_k=5, tags=["filesystem"], registry={})

        # Automatic fallback chain
        provider = get_tool_search_provider("vectordb,local")
        # Tries vectordb first, falls back to local registry
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for tool_search: {provider_names}")
        return ProviderRouter(
            provider_getter=get_tool_search_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    # Register built-in providers on first access
    if not _TOOL_SEARCH_PROVIDERS:
        register_tool_search_provider("local", LocalRegistryProvider)
        register_tool_search_provider("registry", LocalRegistryProvider)
        register_tool_search_provider("vectordb", VectorDBProvider)
        register_tool_search_provider("qdrant", VectorDBProvider)
        register_tool_search_provider("remote", RemoteCatalogProvider)
        register_tool_search_provider("catalog", RemoteCatalogProvider)
        register_tool_search_provider("hybrid", HybridProvider)

    if name not in _TOOL_SEARCH_PROVIDERS:
        available = ", ".join(sorted(_TOOL_SEARCH_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown tool search provider: {name}. "
            f"Available: {available}. "
            f"Register custom providers with register_tool_search_provider()."
        )

    try:
        return _TOOL_SEARCH_PROVIDERS[name]()
    except Exception as e:
        raise ValueError(f"Failed to initialize tool search provider '{name}': {e}") from e
