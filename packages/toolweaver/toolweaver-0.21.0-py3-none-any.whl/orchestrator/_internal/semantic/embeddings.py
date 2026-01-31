"""
Embeddings provider switcher for semantic search.
Supports providers: none | local | openai | azure.
Graceful fallback when dependencies or credentials are missing.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingProvider:
    name: str
    dim: int
    encode: Callable[[list[str]], np.ndarray]
    available: bool = True


def _get_env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _warn_unavailable(provider: str, reason: str) -> EmbeddingProvider:
    logger.warning("Embeddings provider '%s' unavailable: %s", provider, reason)
    return EmbeddingProvider(
        name=provider,
        dim=int(os.getenv("EMBEDDING_DIM", "384")),
        encode=lambda texts: np.zeros((len(texts), int(os.getenv("EMBEDDING_DIM", "384")))),
        available=False,
    )


def _local_provider(model_name: str, dim: int) -> EmbeddingProvider:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - dependency missing in some envs
        return _warn_unavailable("local", f"sentence-transformers not installed ({exc})")

    try:
        model = SentenceTransformer(model_name)
    except Exception as exc:  # pragma: no cover - model load failure
        return _warn_unavailable("local", f"failed to load model {model_name} ({exc})")

    def encode(texts: list[str]) -> np.ndarray:
        return model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    return EmbeddingProvider(name="local", dim=dim, encode=encode, available=True)


def _openai_provider(model_name: str, dim: int) -> EmbeddingProvider:
    try:
        import openai
    except Exception as exc:  # pragma: no cover - dependency missing
        return _warn_unavailable("openai", f"openai not installed ({exc})")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _warn_unavailable("openai", "OPENAI_API_KEY not set")

    client = openai.OpenAI(api_key=api_key)

    def encode(texts: list[str]) -> np.ndarray:
        # Minimal implementation; batches texts in one request
        try:
            resp = client.embeddings.create(model=model_name, input=texts)
            vectors = [np.array(item.embedding, dtype=float) for item in resp.data]
            arr = np.vstack(vectors)
            # Normalize to unit length to mirror SentenceTransformer behavior
            norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
            return cast(np.ndarray, arr / norms)
        except Exception as exc:  # pragma: no cover - network/API path
            logger.warning("OpenAI embeddings failed: %s", exc)
            return np.zeros((len(texts), dim))

    return EmbeddingProvider(name="openai", dim=dim, encode=encode, available=True)


def _azure_provider(model_name: str, dim: int) -> EmbeddingProvider:
    try:
        import openai
    except Exception as exc:  # pragma: no cover - dependency missing
        return _warn_unavailable("azure", f"openai not installed ({exc})")

    endpoint = os.getenv("AZURE_EMBEDDING_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    api_version = (
        os.getenv("AZURE_EMBEDDING_API_VERSION")
        or os.getenv("AZURE_OPENAI_API_VERSION")
        or "2024-08-01-preview"
    )

    if not endpoint or not api_key:
        return _warn_unavailable("azure", "Azure embedding endpoint/api key not configured")

    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=endpoint)

    def encode(texts: list[str]) -> np.ndarray:
        try:
            resp = client.embeddings.create(model=model_name, input=texts)
            vectors = [np.array(item.embedding, dtype=float) for item in resp.data]
            arr = np.vstack(vectors)
            norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
            return cast(np.ndarray, arr / norms)
        except Exception as exc:  # pragma: no cover - network/API path
            logger.warning("Azure embeddings failed: %s", exc)
            return np.zeros((len(texts), dim))

    return EmbeddingProvider(name="azure", dim=dim, encode=encode, available=True)


def get_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("SEMANTIC_EMBEDDINGS_PROVIDER", "none").lower()
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    dim = int(os.getenv("EMBEDDING_DIM", "384"))

    if provider == "none":
        return EmbeddingProvider(
            name="none",
            dim=dim,
            encode=lambda texts: np.zeros((len(texts), dim)),
            available=False,
        )
    if provider == "local":
        return _local_provider(model_name, dim)
    if provider == "openai":
        return _openai_provider(model_name, dim)
    if provider == "azure":
        return _azure_provider(model_name, dim)

    logger.warning("Unknown SEMANTIC_EMBEDDINGS_PROVIDER=%s, defaulting to none", provider)
    return EmbeddingProvider(
        name="none",
        dim=dim,
        encode=lambda texts: np.zeros((len(texts), dim)),
        available=False,
    )
