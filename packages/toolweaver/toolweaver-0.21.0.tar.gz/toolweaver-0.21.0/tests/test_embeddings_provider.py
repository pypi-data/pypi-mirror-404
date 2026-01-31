import sys
import types
from collections.abc import Generator
from typing import Any

import numpy as np
import pytest

from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.tools.vector_search import VectorToolSearchEngine


@pytest.fixture
def simple_catalog() -> ToolCatalog:
    catalog = ToolCatalog()
    catalog.add_tool(
        ToolDefinition(
            name="demo_tool",
            type="function",
            description="Demo tool for embeddings",
            parameters=[ToolParameter(name="x", type="string", description="input")],
            domain="demo",
        )
    )
    return catalog


@pytest.fixture(autouse=True)
def reset_env(monkeypatch: Any) -> Generator[None, None, None]:
    for key in [
        "SEMANTIC_EMBEDDINGS_PROVIDER",
        "EMBEDDING_MODEL",
        "EMBEDDING_DIM",
        "OPENAI_API_KEY",
        "AZURE_EMBEDDING_ENDPOINT",
        "AZURE_EMBEDDING_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.mark.asyncio
async def test_provider_none_indexes_with_zeros(monkeypatch: Any, simple_catalog: ToolCatalog) -> None:
    monkeypatch.setenv("SEMANTIC_EMBEDDINGS_PROVIDER", "none")
    engine = VectorToolSearchEngine(fallback_to_memory=True)

    success = engine.index_catalog(simple_catalog)
    assert success
    assert len(engine.memory_embeddings) == 1
    # Embeddings should be zeros when provider is none
    emb = next(iter(engine.memory_embeddings.values()))
    assert np.allclose(emb, 0.0)


@pytest.mark.asyncio
async def test_provider_local_uses_sentence_transformers(monkeypatch: Any, simple_catalog: ToolCatalog) -> None:
    monkeypatch.setenv("SEMANTIC_EMBEDDINGS_PROVIDER", "local")
    monkeypatch.setenv("EMBEDDING_DIM", "4")

    class FakeModel:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def encode(self, texts: list[str], convert_to_numpy: bool = True, normalize_embeddings: bool = True) -> Any:
            # Return deterministic embeddings
            return np.ones((len(texts), 4))

    fake_module = types.SimpleNamespace(SentenceTransformer=FakeModel)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    engine = VectorToolSearchEngine(fallback_to_memory=True)

    success = engine.index_catalog(simple_catalog)
    assert success
    emb = next(iter(engine.memory_embeddings.values()))
    assert np.allclose(emb, 1.0)
    assert emb.shape[0] == 4


def test_unknown_provider_defaults_to_none(monkeypatch: Any) -> None:
    monkeypatch.setenv("SEMANTIC_EMBEDDINGS_PROVIDER", "bogus")
    engine = VectorToolSearchEngine(fallback_to_memory=True)
    engine._init_embedding_model()
    assert engine.embedding_provider is not None
    assert engine.embedding_provider.name == "none"
    assert engine.embedding_provider.available is False
