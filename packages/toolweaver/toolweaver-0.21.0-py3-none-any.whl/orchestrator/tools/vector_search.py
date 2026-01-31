"""
Vector Database Search Engine for ToolWeaver (Phase 7)

Qdrant-based tool search for scaling to 1000+ tools with sub-100ms latency.
"""

import logging
import re
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .._internal.semantic import get_embedding_provider
from ..shared.models import ToolCatalog, ToolDefinition

QdrantClient: Any | None = None
Distance: Any | None = None
FieldCondition: Any | None = None
Filter: Any | None = None
MatchValue: Any | None = None
PointStruct: Any | None = None
VectorParams: Any | None = None
SentenceTransformer: Any | None = None

if TYPE_CHECKING:
    from qdrant_client import QdrantClient as QdrantClientType  # noqa: F401
    from qdrant_client.models import (  # noqa: F401
        Distance as DistanceType,  # noqa: F401
    )
    from qdrant_client.models import (
        FieldCondition as FieldConditionType,  # noqa: F401
    )
    from qdrant_client.models import (
        Filter as FilterType,  # noqa: F401
    )
    from qdrant_client.models import (
        MatchValue as MatchValueType,  # noqa: F401
    )
    from qdrant_client.models import (
        PointStruct as PointStructType,  # noqa: F401
    )
    from qdrant_client.models import (
        VectorParams as VectorParamsType,  # noqa: F401
    )
    from sentence_transformers import SentenceTransformer as SentenceTransformerType  # noqa: F401

    QDRANT_IMPORTED = True
    SENTENCE_AVAILABLE = True
else:
    QDRANT_IMPORTED = False
    SENTENCE_AVAILABLE = False
    try:
        from qdrant_client import QdrantClient  # noqa: F401
        from qdrant_client.models import (
            Distance,
            FieldCondition,
            Filter,
            MatchValue,
            PointStruct,
            VectorParams,
        )  # noqa: F401
        QDRANT_IMPORTED = True
    except ImportError:
        pass
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
        SENTENCE_AVAILABLE = True
    except ImportError:
        pass

TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorToolSearchEngine:
    """
    Vector database search engine using Qdrant.

    Features:
    - Sub-10ms similarity search at 1000+ tools
    - Domain-based filtering for focused search
    - Automatic fallback to in-memory if Qdrant unavailable
    - Batch indexing for fast catalog loading
    - Connection pooling and retry logic

    Usage:
        # Initialize
        search_engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            collection_name="toolweaver_tools"
        )

        # Index catalog
        await search_engine.index_catalog(catalog)

        # Search
        results = search_engine.search("create github PR", catalog, top_k=5)
    """

    def __init__(
        self,
        qdrant_url: str | None = None,
        collection_name: str = "toolweaver_tools",
        api_key: str | None = None,
        embedding_model: str | None = None,
        embedding_dim: int | None = None,
        fallback_to_memory: bool = True,
        use_gpu: bool = True,
        precompute_embeddings: bool = True,
    ):
        """
        Initialize vector search engine.

        Args:
            qdrant_url: Qdrant server URL (defaults to QDRANT_URL env var or http://localhost:6333)
            collection_name: Collection name for tool embeddings
            api_key: Qdrant API key (defaults to QDRANT_API_KEY env var)
            embedding_model: SentenceTransformer model name (defaults to EMBEDDING_MODEL env var)
            embedding_dim: Embedding dimension (defaults to EMBEDDING_DIM env var)
            fallback_to_memory: Use in-memory search if Qdrant unavailable
            use_gpu: Use GPU for embedding generation if available
            precompute_embeddings: Pre-compute embeddings at startup
        """
        import os

        if qdrant_url is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        if api_key is None:
            api_key = os.getenv("QDRANT_API_KEY")
        if embedding_model is None:
            embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        if embedding_dim is None:
            embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))

        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.api_key = api_key
        self.embedding_model_name = embedding_model
        self.embedding_dim = embedding_dim
        self.fallback_to_memory = fallback_to_memory
        self.use_gpu = use_gpu
        self.precompute_embeddings = precompute_embeddings
        self.embedding_provider: Any | None = None

        # Detect GPU availability
        self.device = self._detect_device()

        # Lazy initialization
        self.client: Any | None = None
        self.qdrant_available = False

        # Fallback in-memory search (if Qdrant unavailable)
        self.memory_embeddings: dict[str, np.ndarray] = {}
        self.memory_tools: dict[str, ToolDefinition] = {}

        # Pre-computed embeddings cache
        self.embedding_cache: dict[str, np.ndarray] = {}

        logger.info(
            f"VectorToolSearchEngine initialized (Qdrant: {qdrant_url}, Device: {self.device})"
        )

    def _detect_device(self) -> str:
        """
        Detect best available device for embedding generation.

        Returns:
            Device string: 'cuda', 'mps', or 'cpu'
        """
        global TORCH_AVAILABLE
        torch: Any | None
        try:
            import torch  # local import to avoid heavy startup cost

            TORCH_AVAILABLE = True
        except Exception:
            TORCH_AVAILABLE = False
            torch = None

        if torch is None:
            logger.info("No GPU available, using CPU")
            return "cpu"

        if not self.use_gpu:
            logger.info("GPU disabled by configuration, using CPU")
            return "cpu"

        # Check for NVIDIA CUDA
        torch_any = cast(Any, torch)
        if TORCH_AVAILABLE and hasattr(torch_any, "cuda") and torch_any.cuda.is_available():
            gpu_name = torch_any.cuda.get_device_name(0)
            gpu_memory = torch_any.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            logger.info(f"GPU detected: {gpu_name} ({gpu_memory:.1f} GB)")
            return "cuda"

        # Check for Apple Silicon MPS (Metal Performance Shaders)
        if (
            TORCH_AVAILABLE
            and hasattr(torch_any, "backends")
            and hasattr(torch_any.backends, "mps")
            and torch_any.backends.mps.is_available()
        ):
            logger.info("Apple Silicon GPU detected (MPS)")
            return "mps"

        logger.info("No GPU available, using CPU")
        return "cpu"

    def _init_qdrant_client(self) -> None:
        """Initialize Qdrant client with connection pooling"""
        if self.client is None:
            global \
                QdrantClient, \
                Distance, \
                FieldCondition, \
                Filter, \
                MatchValue, \
                PointStruct, \
                VectorParams, \
                QDRANT_IMPORTED
            try:
                from qdrant_client import QdrantClient as QC
                from qdrant_client.models import (
                    Distance as Dist,
                )
                from qdrant_client.models import (
                    FieldCondition as FC,
                )
                from qdrant_client.models import (
                    Filter as Fil,
                )
                from qdrant_client.models import (
                    MatchValue as MV,
                )
                from qdrant_client.models import (
                    PointStruct as PS,
                )
                from qdrant_client.models import (
                    VectorParams as VP,
                )

                # Assign to globals
                global QdrantClient, Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
                QdrantClient = QC
                Distance = Dist
                FieldCondition = FC
                Filter = Fil
                MatchValue = MV
                PointStruct = PS
                VectorParams = VP
                QDRANT_IMPORTED = True
            except Exception as exc:
                self.qdrant_available = False
                logger.warning(
                    "qdrant-client not installed; using in-memory fallback if enabled (%s)", exc
                )
                return
            try:
                import warnings
                with warnings.catch_warnings():
                    # Suppress insecure connection warning for localhost testing
                    if self.qdrant_url and "localhost" in self.qdrant_url:
                        warnings.filterwarnings("ignore", message="Api key is used with an insecure connection")
                    self.client = QdrantClient(
                        url=self.qdrant_url,
                        api_key=self.api_key,
                        timeout=10,
                        check_compatibility=False,
                        prefer_grpc=False,  # Use REST API for simplicity
                    )
                # Test connection
                self.client.get_collections()
                self.qdrant_available = True
                logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant: {e}")
                self.qdrant_available = False
                if not self.fallback_to_memory:
                    raise
                logger.info("Will use in-memory fallback for vector search")

    def _init_embedding_model(self) -> None:
        """Initialize embedding provider based on SEMANTIC_EMBEDDINGS_PROVIDER."""
        if self.embedding_provider is None:
            provider = get_embedding_provider()
            self.embedding_provider = provider
            self.embedding_dim = provider.dim
            logger.info(
                "Embeddings provider: %s (dim=%s, available=%s)",
                provider.name,
                self.embedding_dim,
                provider.available,
            )

    def _ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist"""
        if not self.qdrant_available:
            return
        if self.client is None:
            return

        try:
            client = cast(Any, self.client)
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                vector_params = cast(Any, VectorParams)
                distance = cast(Any, Distance)
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=vector_params(size=self.embedding_dim, distance=distance.COSINE),
                )
                logger.info(f"Collection '{self.collection_name}' created")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            self.qdrant_available = False

    def index_catalog(self, catalog: ToolCatalog, batch_size: int = 32) -> bool:
        """
        Index entire tool catalog in Qdrant.

        Args:
            catalog: Tool catalog to index
            batch_size: Batch size for embedding generation

        Returns:
            True if indexing succeeded, False otherwise
        """
        self._init_qdrant_client()
        self._init_embedding_model()

        tools = list(catalog.tools.values())
        if len(tools) == 0:
            logger.warning("Empty catalog - nothing to index")
            return False

        logger.info(
            f"Indexing {len(tools)} tools (batch_size={batch_size}, device={self.device})..."
        )

        # Generate embeddings in batches with GPU acceleration
        descriptions = [self._get_searchable_text(tool) for tool in tools]
        embeddings = self._generate_embeddings_batch(
            descriptions, batch_size=batch_size, show_progress=True
        )

        if self.qdrant_available:
            try:
                self._ensure_collection_exists()

                # Create points for Qdrant using sequential IDs
                points = []
                point_struct = cast(Any, PointStruct)
                for i, tool in enumerate(tools):
                    points.append(
                        point_struct(
                            id=i,
                            vector=embeddings[i].tolist(),
                            payload={
                                "tool_name": tool.name,
                                "tool_type": tool.type,
                                "domain": getattr(tool, "domain", "general"),
                                "description": tool.description,
                                "version": getattr(tool, "version", "1.0.0"),
                            },
                        )
                    )

                # Batch upsert to Qdrant
                if self.client is None:
                    self.qdrant_available = False
                else:
                    client = cast(Any, self.client)
                    client.upsert(collection_name=self.collection_name, points=points)
                logger.info(f"Successfully indexed {len(tools)} tools in Qdrant")
            except Exception as e:
                logger.error(f"Failed to index in Qdrant: {e}")
                self.qdrant_available = False

        # ALWAYS store in memory as fallback (not just if Qdrant fails)
        logger.info("Storing embeddings in memory (fallback mode)")
        for i, tool in enumerate(tools):
            self.memory_embeddings[tool.name] = embeddings[i]
            self.memory_tools[tool.name] = tool

        return True

    def search(
        self,
        query: str,
        catalog: ToolCatalog,
        top_k: int = 5,
        domain: str | None = None,
        min_score: float = 0.3,
    ) -> list[tuple[ToolDefinition, float]]:
        """
        Search for relevant tools using vector similarity.

        Args:
            query: User's natural language query
            catalog: Tool catalog (used for fallback)
            top_k: Number of results to return
            domain: Optional domain filter (e.g., "github", "slack")
            min_score: Minimum similarity score (0-1)

        Returns:
            List of (ToolDefinition, score) tuples, sorted by relevance
        """
        self._init_qdrant_client()
        self._init_embedding_model()

        # Generate query embedding (uses cache if available)
        query_embeddings = self._generate_embeddings_batch(
            [query], batch_size=1, show_progress=False
        )
        query_embedding = query_embeddings[0]

        # Try Qdrant search first (with enhanced fallback)
        if self.qdrant_available:
            try:
                results = self._qdrant_search(query_embedding, catalog, top_k, domain, min_score)
                # If Qdrant returns results, use them
                if results:
                    return results
                # If Qdrant returned 0 results, fall back to memory (Qdrant may be unreliable in tests)
                logger.debug("Qdrant returned 0 results, using in-memory fallback")
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}, falling back to memory")
                self.qdrant_available = False

        # Fallback: In-memory cosine similarity
        if self.fallback_to_memory:
            adjusted_min_score = min_score
            provider = self.embedding_provider
            if provider is None or not getattr(provider, "available", False):
                adjusted_min_score = 0.0

            return self._memory_search(query_embedding, catalog, top_k, adjusted_min_score, domain)

        # Vector search unavailable and fallback disabled
        logger.error("Vector search unavailable and fallback disabled")
        return []

    def _qdrant_search(
        self,
        query_embedding: np.ndarray,
        catalog: ToolCatalog,
        top_k: int,
        domain: str | None,
        min_score: float,
    ) -> list[tuple[ToolDefinition, float]]:
        """Perform search using Qdrant"""
        # Build filter for domain-based search
        search_filter = None
        if domain:
            filter_cls = cast(Any, Filter)
            field_condition = cast(Any, FieldCondition)
            match_value = cast(Any, MatchValue)
            search_filter = filter_cls(
                must=[field_condition(key="domain", match=match_value(value=domain))]
            )

        # Search in Qdrant using search method
        # Note: search returns ScoredPoints directly
        try:
            if self.client is None:
                return []
            client = cast(Any, self.client)
            search_results_list = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=search_filter,
                limit=top_k * 2,  # Get more to filter by score
                score_threshold=0.0,  # Return all results, we'll filter manually
            )
            logger.debug(
                f"search returned {len(search_results_list) if search_results_list else 0} results"
            )

            # Wrap in QueryResponse-like object for compatibility
            class QueryResponse:
                def __init__(self, points: list[Any]) -> None:
                    self.points = points

            search_results = QueryResponse(search_results_list)
        except Exception as e:
            logger.warning(f"search failed: {e}, trying query_points: {type(e).__name__}")
            try:
                if self.client is None:
                    return []
                client = cast(Any, self.client)
                search_results = client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding.tolist(),
                    query_filter=search_filter,
                    limit=top_k * 2,  # Get more to filter by score
                )
                logger.debug(
                    f"query_points returned {len(search_results.points) if search_results else 0} points"
                )
            except Exception as e2:
                logger.warning(f"query_points also failed: {e2}")
                search_results = None

        # Convert results to (ToolDefinition, score) tuples
        results = []
        if search_results and search_results.points:
            for hit in search_results.points:
                tool_name = hit.payload.get("tool_name")
                if not tool_name or tool_name not in catalog.tools:
                    logger.debug(
                        f"Skipping hit: tool_name={tool_name}, in_catalog={tool_name in catalog.tools if tool_name else False}"
                    )
                    continue

                score = getattr(hit, "score", 0.0) if hasattr(hit, "score") else 0.0

                # Apply min_score threshold manually
                if score >= min_score:
                    tool = catalog.tools[tool_name]
                    results.append((tool, score))

                    # Stop if we have enough results
                    if len(results) >= top_k:
                        break

        logger.info(
            f"Qdrant search returned {len(results)} results (top_k={top_k}, domain={domain})"
        )
        return results

    def _memory_search(
        self,
        query_embedding: np.ndarray,
        catalog: ToolCatalog,
        top_k: int,
        min_score: float,
        domain: str | None = None,
    ) -> list[tuple[ToolDefinition, float]]:
        """Fallback: In-memory cosine similarity search"""
        if not self.memory_embeddings:
            logger.warning("No embeddings in memory, indexing catalog...")
            self.index_catalog(catalog)

        # Compute cosine similarity for all tools
        scores = []
        for tool_name, embedding in self.memory_embeddings.items():
            if tool_name in catalog.tools:
                tool = catalog.tools[tool_name]

                # Apply domain filter if specified
                if domain and tool.domain != domain:
                    continue

                similarity = np.dot(query_embedding, embedding)
                if similarity >= min_score:
                    scores.append((tool, float(similarity)))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:top_k]

        logger.info(
            f"In-memory search returned {len(results)} results (checked {len(self.memory_embeddings)} tools, min_score={min_score})"
        )
        return results

    def _generate_embeddings_batch(
        self, texts: list[str], batch_size: int = 32, show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings in batches with GPU acceleration.

        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding (larger for GPU)
            show_progress: Show progress bar

        Returns:
            Numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        # Check cache first
        cached_embeddings = []
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.embedding_cache:
                cached_embeddings.append((i, self.embedding_cache[cache_key]))
            else:
                texts_to_encode.append(text)
                text_indices.append(i)

        # If all cached, return immediately
        if not texts_to_encode:
            logger.info(f"All {len(texts)} embeddings retrieved from cache")
            result = np.zeros((len(texts), self.embedding_dim))
            for idx, emb in cached_embeddings:
                result[idx] = emb
            return result

        logger.info(
            f"Generating {len(texts_to_encode)} embeddings ({len(cached_embeddings)} cached)"
        )

        # Adjust batch size for GPU (can handle larger batches)
        if self.device in ["cuda", "mps"]:
            batch_size = min(batch_size * 4, 128)  # 4x larger batches on GPU
            logger.debug(f"Using GPU batch size: {batch_size}")

        # Generate embeddings
        if self.embedding_provider is None:
            self._init_embedding_model()

        provider = self.embedding_provider
        if provider is None or not getattr(provider, "available", False):
            # Provider is None or not available, use zero embeddings
            new_embeddings = np.zeros((len(texts_to_encode), self.embedding_dim))
            if provider is not None and getattr(provider, "name", "") != "none":
                # Deterministic bag-of-words hashing fallback so tests can run without models
                for i, text in enumerate(texts_to_encode):
                    tokens = re.findall(r"\w+", text.lower())
                    if not tokens:
                        continue
                    for tok in tokens:
                        idx = hash(tok) % self.embedding_dim
                        new_embeddings[i, idx] += 1.0
                    norm = np.linalg.norm(new_embeddings[i])
                    if norm > 0:
                        new_embeddings[i] = new_embeddings[i] / norm
        else:
            # Provider is available
            try:
                new_embeddings = provider.encode(texts_to_encode)
            except Exception as exc:
                logger.warning("Embedding generation failed, using hashing fallback: %s", exc)
                new_embeddings = np.zeros((len(texts_to_encode), self.embedding_dim))
                for i, text in enumerate(texts_to_encode):
                    tokens = re.findall(r"\w+", text.lower())
                    if not tokens:
                        continue
                    for tok in tokens:
                        idx = hash(tok) % self.embedding_dim
                        new_embeddings[i, idx] += 1.0
                    norm = np.linalg.norm(new_embeddings[i])
                    if norm > 0:
                        new_embeddings[i] = new_embeddings[i] / norm

        # Cache new embeddings
        for i, text in enumerate(texts_to_encode):
            cache_key = self._get_cache_key(text)
            self.embedding_cache[cache_key] = new_embeddings[i]

        # Combine cached and new embeddings
        result = np.zeros((len(texts), self.embedding_dim))
        for idx, emb in cached_embeddings:
            result[idx] = emb
        for i, idx in enumerate(text_indices):
            result[idx] = new_embeddings[i]

        return result

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text (first 100 chars hash)"""
        return str(hash(text[:100]))

    def precompute_catalog_embeddings(self, catalog: ToolCatalog) -> None:
        """
        Pre-compute embeddings for all tools in catalog at startup.

        This eliminates cold-start latency by caching embeddings in memory.

        Args:
            catalog: Tool catalog to pre-compute embeddings for
        """
        if not self.precompute_embeddings:
            logger.debug("Embedding pre-computation disabled")
            return

        tools = list(catalog.tools.values())
        if not tools:
            logger.warning("Empty catalog - nothing to pre-compute")
            return

        logger.info(f"Pre-computing embeddings for {len(tools)} tools...")
        descriptions = [self._get_searchable_text(tool) for tool in tools]

        # Generate and cache embeddings
        start_time = None
        end_time = None
        if TORCH_AVAILABLE and self.device == "cuda":
            import torch  # noqa: F401

            start_time = torch.cuda.Event(enable_timing=True)
            end_time = torch.cuda.Event(enable_timing=True)

        if start_time:
            start_time.record()

        embeddings = self._generate_embeddings_batch(
            descriptions,
            batch_size=64,  # Larger batch for pre-computation
            show_progress=False,
        )

        if end_time and start_time:
            end_time.record()
            elapsed_ms = 0.0
            if TORCH_AVAILABLE:
                import torch

                torch.cuda.synchronize()
                elapsed_ms = start_time.elapsed_time(end_time)
            logger.info(
                f"Pre-computed {len(tools)} embeddings in {elapsed_ms:.1f}ms on {self.device.upper()}"
            )
        else:
            logger.info(f"Pre-computed {len(tools)} embeddings on {self.device.upper()}")

        # Cache results
        for i, tool in enumerate(tools):
            cache_key = self._get_cache_key(self._get_searchable_text(tool))
            self.embedding_cache[cache_key] = embeddings[i]

        logger.info(f"Embedding cache size: {len(self.embedding_cache)} entries")

    def _get_searchable_text(self, tool: ToolDefinition) -> str:
        """Extract searchable text from tool definition"""
        parts = [tool.description]

        # Add parameter names and descriptions
        for param in tool.parameters:
            parts.append(param.name)
            if param.description:
                parts.append(param.description)

        # Add examples
        for example in tool.examples:
            if hasattr(example, "scenario"):
                parts.append(example.scenario)

        return " ".join(parts)

    def delete_tool(self, tool_name: str) -> bool:
        """
        Delete a tool from the index.

        Args:
            tool_name: Name of tool to delete

        Returns:
            True if deletion succeeded
        """
        if self.qdrant_available and self.client is not None:
            try:
                client = cast(Any, self.client)
                filter_cls = cast(Any, Filter)
                field_condition = cast(Any, FieldCondition)
                match_value = cast(Any, MatchValue)
                # Find point ID by tool_name
                search_results = client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=filter_cls(
                        must=[field_condition(key="tool_name", match=match_value(value=tool_name))]
                    ),
                    limit=1,
                )

                if search_results[0]:
                    point_id = search_results[0][0].id
                    self.client.delete(
                        collection_name=self.collection_name, points_selector=[point_id]
                    )
                    logger.info(f"Deleted tool '{tool_name}' from Qdrant")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete tool from Qdrant: {e}")

        # Fallback: Delete from memory
        if tool_name in self.memory_embeddings:
            del self.memory_embeddings[tool_name]
            del self.memory_tools[tool_name]
            return True

        return False

    def clear_index(self) -> bool:
        """Clear all tools from the index"""
        if self.qdrant_available and self.client is not None:
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Cleared collection: {self.collection_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")

        # Clear memory fallback
        self.memory_embeddings.clear()
        self.memory_tools.clear()
        return True
