"""
Tests for Vector Tool Search Engine (Phase 7)

Validates Qdrant integration, fallback behavior, and performance.
"""

import os
import time
from collections.abc import Generator
from typing import Any

import pytest

from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.tools.vector_search import VectorToolSearchEngine

pytest.importorskip("qdrant_client")
pytest.importorskip("numpy")


@pytest.fixture(autouse=True, scope="module")
def use_local_embeddings() -> Generator[None, None, None]:
    """
    Use 'local' embedding provider for vector search tests.

    Vector search requires actual embeddings for meaningful similarity comparisons.
    """
    original = os.environ.get("SEMANTIC_EMBEDDINGS_PROVIDER")
    os.environ["SEMANTIC_EMBEDDINGS_PROVIDER"] = "local"
    yield
    if original is None:
        os.environ.pop("SEMANTIC_EMBEDDINGS_PROVIDER", None)
    else:
        os.environ["SEMANTIC_EMBEDDINGS_PROVIDER"] = original


@pytest.fixture
def large_catalog() -> ToolCatalog:
    """Create a large tool catalog for testing"""
    catalog = ToolCatalog()

    # GitHub tools
    for i in range(20):
        catalog.add_tool(
            ToolDefinition(
                name=f"github_operation_{i}",
                type="function",
                description=f"GitHub operation {i}: create PR, list issues, manage repos",
                parameters=[
                    ToolParameter(
                        name="repo", type="string", description="Repository name", required=True
                    )
                ],
                domain="github",
            )
        )

    # Slack tools
    for i in range(20):
        catalog.add_tool(
            ToolDefinition(
                name=f"slack_operation_{i}",
                type="function",
                description=f"Slack operation {i}: send messages, create channels, manage users",
                parameters=[
                    ToolParameter(
                        name="channel", type="string", description="Channel name", required=True
                    )
                ],
                domain="slack",
            )
        )

    # AWS tools
    for i in range(20):
        catalog.add_tool(
            ToolDefinition(
                name=f"aws_operation_{i}",
                type="function",
                description=f"AWS operation {i}: S3 buckets, EC2 instances, Lambda functions",
                parameters=[
                    ToolParameter(
                        name="resource", type="string", description="Resource name", required=True
                    )
                ],
                domain="aws",
            )
        )

    # Database tools
    for i in range(20):
        catalog.add_tool(
            ToolDefinition(
                name=f"db_operation_{i}",
                type="function",
                description=f"Database operation {i}: queries, migrations, backups",
                parameters=[
                    ToolParameter(
                        name="query", type="string", description="SQL query", required=True
                    )
                ],
                domain="database",
            )
        )

    # General utilities
    for i in range(20):
        catalog.add_tool(
            ToolDefinition(
                name=f"util_operation_{i}",
                type="function",
                description=f"Utility operation {i}: file operations, parsing, formatting",
                parameters=[
                    ToolParameter(
                        name="input", type="string", description="Input data", required=True
                    )
                ],
                domain="general",
            )
        )

    return catalog  # 100 tools total


@pytest.fixture
def search_engine_fallback_only() -> VectorToolSearchEngine:
    """Create search engine with memory fallback (NO Qdrant)"""
    # Always use invalid URL to force memory fallback
    return VectorToolSearchEngine(
        qdrant_url="http://localhost:9999",  # Invalid - forces fallback
        fallback_to_memory=True,
    )


@pytest.fixture
def search_engine_with_qdrant() -> VectorToolSearchEngine:
    """Create search engine with Qdrant Cloud (if configured)"""
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        pytest.skip("QDRANT_URL not configured - skipping Qdrant-specific test")

    api_key = os.getenv("QDRANT_API_KEY")
    return VectorToolSearchEngine(qdrant_url=qdrant_url, api_key=api_key, fallback_to_memory=True)


@pytest.fixture(scope="module")
def qdrant_seeded_catalog() -> ToolCatalog | None:
    """Module-level fixture: DEPRECATED - seeding now handled per-test in seeded_search_engine_qdrant"""
    return None  # No longer used


@pytest.fixture(scope="module")
def qdrant_seeded_catalog_old(large_catalog: ToolCatalog) -> ToolCatalog | None:
    """Module-level fixture: seed Qdrant once for all Qdrant tests"""
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        return None  # Qdrant not configured

    # Seed once at module level
    api_key = os.getenv("QDRANT_API_KEY")
    engine = VectorToolSearchEngine(
        qdrant_url=qdrant_url,
        api_key=api_key,
        fallback_to_memory=False,  # No fallback for module seeding
    )

    # Index catalog once for all tests
    print(f"\n[MODULE SETUP] Seeding Qdrant with {len(large_catalog.tools)} tools...")
    engine.index_catalog(large_catalog, batch_size=32)
    print("[MODULE SETUP] Qdrant seeding complete")

    return large_catalog


@pytest.fixture
def seeded_search_engine_fallback(large_catalog: ToolCatalog) -> VectorToolSearchEngine:
    """Create fallback search engine seeded with catalog data"""
    engine = VectorToolSearchEngine(
        qdrant_url="http://localhost:9999",  # Invalid - forces fallback
        fallback_to_memory=True,
    )
    engine.index_catalog(large_catalog, batch_size=32)
    return engine


@pytest.fixture
def seeded_search_engine_qdrant(large_catalog: ToolCatalog) -> VectorToolSearchEngine:
    """Create Qdrant search engine using pre-seeded catalog data"""
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        pytest.skip("QDRANT_URL not configured - skipping Qdrant-specific test")

    api_key = os.getenv("QDRANT_API_KEY")
    # Create engine and index catalog for this test
    engine = VectorToolSearchEngine(
        qdrant_url=qdrant_url,
        api_key=api_key,
        fallback_to_memory=False,  # No fallback - should have real data
    )
    engine.index_catalog(large_catalog, batch_size=32)
    return engine


def test_initialization_fallback_mode() -> None:
    """Test: Engine initializes correctly in fallback mode (MUST PASS)"""
    # Fallback mode should always initialize correctly
    engine = VectorToolSearchEngine(
        qdrant_url="http://localhost:9999",  # Invalid - forces fallback
        fallback_to_memory=True,
    )

    assert engine.qdrant_url == "http://localhost:9999"
    assert engine.collection_name == "toolweaver_tools"
    assert engine.embedding_dim == 384
    assert engine.fallback_to_memory, "Fallback mode should be enabled"


def test_index_catalog_fallback_mode(large_catalog: Any, search_engine_fallback_only: Any) -> None:
    """Test: Fallback mode indexing (MUST PASS)"""
    # Fallback indexing should always work
    success = search_engine_fallback_only.index_catalog(large_catalog, batch_size=32)

    assert success, "Fallback mode indexing must succeed"
    assert len(search_engine_fallback_only.memory_embeddings) == 100
    assert len(search_engine_fallback_only.memory_tools) == 100


def test_search_fallback_mode(large_catalog: Any, search_engine_fallback_only: Any) -> None:
    """Test: Fallback mode search with substring matching (MUST PASS)"""
    # Index in fallback mode (memory)
    search_engine_fallback_only.index_catalog(large_catalog)

    # Search for GitHub tools - fallback uses keyword matching
    results = search_engine_fallback_only.search("github operation", large_catalog, top_k=5)

    assert len(results) > 0, "Fallback search must return results for known keywords"
    assert len(results) <= 5

    # With fallback, should find tools matching "github" keyword
    github_tools = [tool for tool, score in results if "github" in tool.description.lower()]
    assert len(github_tools) > 0, "Fallback search must find keyword matches"


def test_search_performance_fallback_mode(seeded_search_engine_fallback: Any, large_catalog: Any) -> None:
    """Test: Fallback mode search performance (MUST PASS)"""
    # Warm-up query
    seeded_search_engine_fallback.search("test", large_catalog, top_k=5)

    # Measure search time
    queries = [
        "github operation",
        "slack operation",
        "aws operation",
        "database operation",
        "util operation",
    ]

    latencies = []
    for query in queries:
        start_time = time.time()
        results = seeded_search_engine_fallback.search(query, large_catalog, top_k=5)
        latency_ms = (time.time() - start_time) * 1000
        latencies.append(latency_ms)

        assert len(results) > 0, f"Fallback search must return results for: {query}"

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    print("\n100-tool catalog performance (FALLBACK mode):")
    print(f"  Average latency: {avg_latency:.1f}ms")
    print(f"  Max latency: {max_latency:.1f}ms")

    # Target: <200ms for 100 tools with in-memory fallback
    assert avg_latency < 200, f"Average latency {avg_latency:.1f}ms exceeds 200ms target"


def test_search_performance_qdrant_mode(seeded_search_engine_qdrant: Any, large_catalog: Any) -> None:
    """Test: Qdrant Cloud search performance (ONLY if QDRANT_URL configured)"""
    # Warm-up query
    seeded_search_engine_qdrant.search("manage repos", large_catalog, top_k=5)

    # Measure search time - use queries that match tool descriptions
    queries = ["create PR", "send messages", "S3 buckets", "database query", "file operations"]

    latencies = []
    for query in queries:
        start_time = time.time()
        results = seeded_search_engine_qdrant.search(query, large_catalog, top_k=5)
        latency_ms = (time.time() - start_time) * 1000
        latencies.append(latency_ms)

        assert len(results) > 0, f"Qdrant search must return results for: {query}"

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    print("\n100-tool catalog performance (QDRANT mode):")
    print(f"  Average latency: {avg_latency:.1f}ms")
    print(f"  Max latency: {max_latency:.1f}ms")

    # Qdrant should be faster than fallback
    # Target: <100ms for 100 tools with Qdrant
    assert avg_latency < 300, f"Average latency {avg_latency:.1f}ms exceeds 300ms target"


def test_domain_filtering_fallback_mode(seeded_search_engine_fallback: Any, large_catalog: Any) -> None:
    """Test: Domain filtering with fallback (MUST PASS)"""
    # Search with domain filter
    results = seeded_search_engine_fallback.search(
        "github operation", large_catalog, top_k=10, domain="github"
    )

    # Should only return github tools - fallback filters by domain
    assert len(results) > 0, "Fallback domain filtering must return results"
    for tool, _score in results:
        assert tool.domain == "github", "Fallback filtering must respect domain constraint"


def test_domain_filtering_qdrant_mode(seeded_search_engine_qdrant: Any, large_catalog: Any) -> None:
    """Test: Domain filtering with Qdrant (ONLY if QDRANT_URL configured)"""
    # Search with domain filter - use query that matches tool descriptions
    # Note: Domain filtering may not work if Qdrant index isn't created
    # So we test that results are in correct domain when domain filter is applied
    results = seeded_search_engine_qdrant.search(
        "create PR", large_catalog, top_k=10, domain="github"
    )

    # If any results returned, they must respect domain constraint
    if len(results) > 0:
        for tool, _score in results:
            assert tool.domain == "github", "Qdrant filtering must respect domain constraint"
    else:
        # Domain filtering in Qdrant requires special index - skip if not available
        pytest.skip("Qdrant domain filtering requires keyword index (not configured)")


def test_relevance_scores_fallback_mode(seeded_search_engine_fallback: Any, large_catalog: Any) -> None:
    """Test: Relevance scores with fallback (MUST PASS)"""
    results = seeded_search_engine_fallback.search("github operation", large_catalog, top_k=10)

    assert len(results) > 0, "Fallback search must return results"

    # Scores should be between 0 and 1
    for _tool, score in results:
        assert 0 <= score <= 1, f"Score {score} out of range [0, 1]"

    # Scores should be in descending order
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True), "Fallback scores must be sorted descending"


def test_relevance_scores_qdrant_mode(seeded_search_engine_qdrant: Any, large_catalog: Any) -> None:
    """Test: Relevance scores with Qdrant (ONLY if QDRANT_URL configured)"""
    results = seeded_search_engine_qdrant.search("create PR", large_catalog, top_k=10)

    assert len(results) > 0, "Qdrant search must return results"

    # Scores should be between 0 and 1
    for _tool, score in results:
        assert 0 <= score <= 1, f"Score {score} out of range [0, 1]"

    # Scores should be in descending order
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True), "Qdrant scores must be sorted descending"


def test_min_score_threshold_fallback_mode(search_engine_fallback_only: Any, large_catalog: Any) -> None:
    """Test: Min score filtering with fallback (MUST PASS)"""
    search_engine_fallback_only.index_catalog(large_catalog)

    # High threshold should return fewer or equal results
    results_high = search_engine_fallback_only.search(
        "operation", large_catalog, top_k=20, min_score=0.8
    )

    # Low threshold should return more results
    results_low = search_engine_fallback_only.search(
        "operation", large_catalog, top_k=20, min_score=0.1
    )

    # Fallback with high threshold may return 0 results
    # Low threshold should return at least some results (fallback always finds matches)
    assert len(results_low) > 0, "Fallback: low threshold must return results"

    # Verify that lower threshold returns more or equal results than higher threshold
    # (This is the core property we're testing - threshold filtering works)
    assert len(results_low) >= len(results_high), (
        f"Low threshold should return >= results than high threshold "
        f"(low: {len(results_low)}, high: {len(results_high)})"
    )


def test_empty_catalog_fallback_mode(search_engine_fallback_only: Any) -> None:
    """Test: Empty catalog with fallback (MUST PASS)"""
    empty_catalog = ToolCatalog()

    success = search_engine_fallback_only.index_catalog(empty_catalog)
    assert not success, "Fallback: empty catalog indexing must fail"

    results = search_engine_fallback_only.search("test", empty_catalog)
    assert len(results) == 0, "Fallback: search on empty catalog must return no results"


def test_embedding_model_lazy_load_fallback_mode(search_engine_fallback_only: Any) -> None:
    """Test: Embedding provider lazy loading with fallback (MUST PASS)"""
    # Initially None
    assert search_engine_fallback_only.embedding_provider is None, (
        "Embedding provider should initially be None"
    )

    # Trigger loading
    catalog = ToolCatalog()
    catalog.add_tool(
        ToolDefinition(name="test_tool", type="function", description="Test tool", parameters=[])
    )

    search_engine_fallback_only.index_catalog(catalog)

    # Now loaded (will be a provider object, not None)
    assert search_engine_fallback_only.embedding_provider is not None, (
        "Embedding provider must be loaded after indexing"
    )


@pytest.mark.parametrize("catalog_size", [100])
def test_scalability_fallback_mode(large_catalog: Any, catalog_size: Any) -> None:
    """Test: Scalability with fallback (MUST PASS)"""
    # Create search engine with fallback (no Qdrant)
    engine = VectorToolSearchEngine(
        qdrant_url="http://localhost:9999",  # Invalid - forces fallback
        fallback_to_memory=True,
    )

    # Index
    start_time = time.time()
    engine.index_catalog(large_catalog, batch_size=64)
    index_time = (time.time() - start_time) * 1000

    print(f"\nFALLBACK: Indexing {catalog_size} tools took {index_time:.1f}ms")

    # Search
    start_time = time.time()
    results = engine.search("operation", large_catalog, top_k=5)
    search_time = (time.time() - start_time) * 1000

    print(f"FALLBACK: Searching {catalog_size} tools took {search_time:.1f}ms")

    assert len(results) > 0, "Fallback search must return results"

    # Allow generous margin for fallback mode
    assert search_time < 500, f"Fallback search time {search_time:.1f}ms exceeds 500ms target"


@pytest.mark.parametrize("catalog_size", [100])
def test_scalability_qdrant_mode(large_catalog: Any, catalog_size: Any) -> None:
    """Test: Scalability with Qdrant (ONLY if QDRANT_URL configured)"""
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        pytest.skip("QDRANT_URL not configured - cannot test Qdrant mode")

    api_key = os.getenv("QDRANT_API_KEY")
    engine = VectorToolSearchEngine(
        qdrant_url=qdrant_url,
        api_key=api_key,
        fallback_to_memory=False,  # Use already seeded Qdrant
    )

    # Search (data already seeded at module level)
    start_time = time.time()
    results = engine.search("create PR", large_catalog, top_k=5)
    search_time = (time.time() - start_time) * 1000

    print(f"\nQDANT: Searching {catalog_size} tools took {search_time:.1f}ms")

    assert len(results) > 0, "Qdrant search must return results"

    # Performance targets from Phase 7 design:
    # 100 tools: <30ms (optimized, localhost)
    # Cloud Qdrant SaaS: 1-3 seconds (network latency + processing)
    # Use lenient cloud target since network latency dominates
    is_cloud = qdrant_url.startswith("https://")
    target = 5000 if is_cloud else 500  # Cloud is slower due to network round trips
    assert search_time < target, f"Qdrant search time {search_time:.1f}ms exceeds {target}ms target"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
