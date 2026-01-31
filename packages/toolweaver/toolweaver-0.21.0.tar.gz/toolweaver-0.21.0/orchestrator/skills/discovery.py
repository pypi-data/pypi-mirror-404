"""
Semantic Skill Discovery using Qdrant

Optional module for semantic search over skills using existing Qdrant infrastructure.
Falls back gracefully if Qdrant not available.

Usage:
    from orchestrator.skills.discovery import SemanticSkillDiscovery

    discovery = SemanticSkillDiscovery(qdrant_client)
    discovery.index_all_skills()

    # Semantic search
    results = discovery.search("I need to reduce API costs")
    # Returns: [cost-control, budget-optimizer, ...]
"""

import logging
from typing import Any

try:
    from qdrant_client.models import Distance, PointStruct, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from orchestrator.skills import SkillMetadata, SkillRegistry

logger = logging.getLogger(__name__)

# Deferred embedding model loading (avoid import overhead at startup)
_embedding_model: Any = None
_SENTENCE_TRANSFORMERS_AVAILABLE = False


def _get_embedding_model() -> Any:
    """Get or create embedding model (lazy loaded)."""
    global _embedding_model, _SENTENCE_TRANSFORMERS_AVAILABLE

    if _embedding_model is not None:
        return _embedding_model

    import os

    backend = os.getenv("EMBEDDING_BACKEND", "sentence-transformers").lower()
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    try:
        if backend == "sentence-transformers":
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer(model_name)
            _SENTENCE_TRANSFORMERS_AVAILABLE = True
            logger.info(f"Loaded sentence-transformers embedding model: {model_name}")
        elif backend == "openai":
            from orchestrator.skills.openai_embeddings import OpenAIEmbeddingModel

            _embedding_model = OpenAIEmbeddingModel(model_name)
            _SENTENCE_TRANSFORMERS_AVAILABLE = True
            logger.info(f"Loaded OpenAI embedding model: {model_name}")
        elif backend == "azure":
            from orchestrator.skills.azure_embeddings import (
                AzureEmbeddingModel,
            )

            _embedding_model = AzureEmbeddingModel(model_name)
            _SENTENCE_TRANSFORMERS_AVAILABLE = True
            logger.info(f"Loaded Azure OpenAI embedding model: {model_name}")
        elif backend == "ollama":
            from orchestrator.skills.ollama_embeddings import (
                OllamaEmbeddingModel,
            )

            _embedding_model = OllamaEmbeddingModel(model_name)
            _SENTENCE_TRANSFORMERS_AVAILABLE = True
            logger.info(f"Loaded Ollama embedding model: {model_name}")
        else:
            logger.warning(f"Unknown embedding backend: {backend}")
            _SENTENCE_TRANSFORMERS_AVAILABLE = False
            return None
        return _embedding_model
    except ImportError as e:
        logger.warning(
            f"{backend} backend not available. Install with: "
            f"pip install sentence-transformers (for sentence-transformers) or "
            f"configure EMBEDDING_BACKEND in .env. Error: {e}"
        )
        _SENTENCE_TRANSFORMERS_AVAILABLE = False
        return None
    except Exception as e:
        logger.warning(f"Failed to load embedding model ({backend}/{model_name}): {e}")
        _SENTENCE_TRANSFORMERS_AVAILABLE = False
        return None


class SemanticSkillDiscovery:
    """
    Semantic skill discovery using Qdrant vector search.

    Indexes skill metadata (name, description, capabilities) as embeddings
    for semantic search. Uses existing Qdrant infrastructure.

    Falls back to text search if Qdrant not available.
    """

    COLLECTION_NAME = "toolweaver_skills"
    # EMBEDDING_DIM determined by EMBEDDING_MODEL in .env (default: 384 for all-MiniLM-L6-v2)

    def __init__(self, qdrant_client: Any | None = None, registry: SkillRegistry | None = None) -> None:
        """Initialize semantic skill discovery.

        Args:
            qdrant_client: QdrantClient instance (optional)
            registry: SkillRegistry instance (defaults to global)
        """
        import os

        self.embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))
        self.qdrant = qdrant_client
        self.registry = registry or SkillRegistry()
        self.enabled = QDRANT_AVAILABLE and qdrant_client is not None

        if not self.enabled:
            logger.warning(
                "Qdrant not available - semantic search disabled. "
                "Install qdrant-client for semantic search."
            )

    def _ensure_collection(self) -> None:
        """Ensure Qdrant collection exists."""
        if not self.enabled or not self.qdrant:
            return

        try:
            # Check if collection exists
            collections = self.qdrant.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.COLLECTION_NAME not in collection_names:
                # Create collection
                self.qdrant.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            self.enabled = False

    def _create_skill_text(self, skill: SkillMetadata) -> str:
        """Create searchable text from skill metadata.

        Args:
            skill: Skill metadata

        Returns:
            Combined text for embedding
        """
        parts = [
            skill.name,
            skill.description,
            " ".join(skill.categories),
            " ".join(skill.tags),
        ]

        # Add capability descriptions
        for capability in skill.capabilities:
            parts.append(capability.name)
            parts.append(capability.description)

        return " ".join(parts)

    def _embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using sentence-transformers.

        Uses real embeddings if sentence-transformers is available,
        falls back to deterministic hash-based embeddings otherwise.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (384 dimensions)
        """
        # Try to use real embeddings
        if _SENTENCE_TRANSFORMERS_AVAILABLE or _get_embedding_model() is not None:
            try:
                model = _get_embedding_model()
                if model:
                    embedding = model.encode(text)
                    return embedding.tolist()
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}, using fallback")

        # Fallback: deterministic hash-based embedding
        import hashlib
        import struct

        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float vector
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i : i + 4]
            if len(chunk) == 4:
                value = struct.unpack("!f", chunk)[0]
                vector.append(value)

        # Pad or trim to embedding dimension
        while len(vector) < self.embedding_dim:
            vector.append(0.0)
        vector = vector[: self.embedding_dim]

        # Normalize
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    def index_skill(self, skill_name: str) -> bool:
        """Index a single skill for semantic search.

        Args:
            skill_name: Name of skill to index

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            metadata = self.registry.get_metadata(skill_name)
            if not metadata:
                return False

            self._ensure_collection()

            # Create searchable text
            text = self._create_skill_text(metadata)

            # Generate embedding
            embedding = self._embed_text(text)

            # Use hashed skill name as UUID-compatible ID (Qdrant Cloud limitation)
            import hashlib

            skill_hash = int(hashlib.md5(skill_name.encode()).hexdigest()[:8], 16)

            # Index in Qdrant
            point = PointStruct(
                id=skill_hash,
                vector=embedding,
                payload={"skill_name": skill_name, **metadata.to_dict()},
            )

            if self.qdrant:
                self.qdrant.upsert(collection_name=self.COLLECTION_NAME, points=[point])

            logger.debug(f"Indexed skill: {skill_name}")
            return True

        except Exception as e:
            logger.error(f"Error indexing skill {skill_name}: {e}")
            return False

    def index_all_skills(self) -> int:
        """Index all skills in registry.

        Returns:
            Number of skills indexed
        """
        if not self.enabled:
            logger.warning("Qdrant not available - cannot index skills")
            return 0

        skills = self.registry.list_skills()
        count = 0

        for skill_name in skills:
            if self.index_skill(skill_name):
                count += 1

        logger.info(f"Indexed {count}/{len(skills)} skills")
        return count

    def search(
        self, query: str, limit: int = 5, score_threshold: float = 0.5
    ) -> list[SkillMetadata]:
        """Semantic search for skills.

        Args:
            query: Natural language query
            limit: Maximum results
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of matching skill metadata
        """
        if not self.enabled:
            # Fall back to text search
            logger.debug("Falling back to text search (Qdrant not available)")
            return self.registry.search(query, limit)

        try:
            # Generate query embedding
            query_embedding = self._embed_text(query)

            # Search Qdrant
            if not self.qdrant:
                return []
            results = self.qdrant.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Convert to SkillMetadata objects
            skills = []
            for result in results:
                # Get skill name from payload
                skill_name = result.payload.get("skill_name")
                if skill_name:
                    metadata = self.registry.get_metadata(skill_name)
                    if metadata:
                        skills.append(metadata)

            return skills

        except Exception as e:
            logger.error(f"Error searching skills: {e}")
            # Fall back to text search
            return self.registry.search(query, limit)

    def search_by_capability(self, capability_query: str, limit: int = 5) -> list[SkillMetadata]:
        """Search for skills by capability description.

        Args:
            capability_query: What you want to do
            limit: Maximum results

        Returns:
            List of skills with matching capabilities
        """
        # Enhance query to focus on capabilities
        enhanced_query = f"capability: {capability_query}"
        return self.search(enhanced_query, limit)

    def get_similar_skills(self, skill_name: str, limit: int = 5) -> list[SkillMetadata]:
        """Find skills similar to a given skill.

        Args:
            skill_name: Reference skill name
            limit: Maximum results

        Returns:
            List of similar skills
        """
        metadata = self.registry.get_metadata(skill_name)
        if not metadata:
            return []

        # Use skill description as query
        query = metadata.description
        results = self.search(query, limit + 1)  # +1 to exclude self

        # Filter out the reference skill
        return [s for s in results if s.name != skill_name][:limit]


def create_discovery(qdrant_client: Any | None = None) -> SemanticSkillDiscovery:
    """Create semantic skill discovery instance.

    Args:
        qdrant_client: QdrantClient instance (optional)

    Returns:
        SemanticSkillDiscovery instance
    """
    return SemanticSkillDiscovery(qdrant_client=qdrant_client)


__all__ = ["SemanticSkillDiscovery", "create_discovery", "QDRANT_AVAILABLE"]
