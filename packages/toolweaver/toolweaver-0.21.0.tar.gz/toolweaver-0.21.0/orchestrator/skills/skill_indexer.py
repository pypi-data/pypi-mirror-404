"""
Semantic Skill Indexer

Indexes skills in Qdrant vector database for semantic search.
Enables finding skills by capability, description, or natural language queries.
"""

import json
from pathlib import Path
from typing import Any, cast

import yaml

QdrantClient: Any | None = None

try:
    from qdrant_client import QdrantClient as _QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError:
    QDRANT_AVAILABLE = False
else:
    QdrantClient = _QdrantClient
    QDRANT_AVAILABLE = True

SentenceTransformer: Any | None = None

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
except ImportError:
    TRANSFORMERS_AVAILABLE = False
except ValueError:
    # Handle the "openai.__spec__ is not set" case during test collection
    TRANSFORMERS_AVAILABLE = False
else:
    SentenceTransformer = _SentenceTransformer
    TRANSFORMERS_AVAILABLE = True



class SkillIndexer:
    """Index and search skills using semantic embeddings."""

    def __init__(self, qdrant_url: str = ":memory:", collection_name: str = "skills"):
        """Initialize the skill indexer.

        Args:
            qdrant_url: Qdrant instance URL (default: in-memory)
            collection_name: Name of the Qdrant collection
        """
        import os

        backend = os.getenv("EMBEDDING_BACKEND", "sentence-transformers").lower()
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))

        if backend == "sentence-transformers":
            model_cls = cast(Any, SentenceTransformer)
            self.model: Any | None = model_cls(model_name)
        else:
            # For other backends, get_embedding_model() will handle initialization
            self.model = None

        self.embedding_dim = embedding_dim
        client_cls = cast(Any, QdrantClient)
        self.client = client_cls(qdrant_url)
        self.collection_name = collection_name
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the Qdrant collection for skills."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except Exception:
            pass  # Collection doesn't exist yet

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
        )
        self._initialized = True

    def _load_skill_metadata(self, skill_name: str) -> dict[str, Any] | None:
        """Load skill metadata from skill.yaml.

        Args:
            skill_name: Name of the skill (directory name)

        Returns:
            Skill metadata dict or None if not found
        """
        skill_yaml = Path("orchestrator/skills") / skill_name / "skill.yaml"

        if not skill_yaml.exists():
            return None

        try:
            with open(skill_yaml) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {skill_name}: {e}")
            return None

    def _generate_skill_description(self, metadata: dict[str, Any]) -> str:
        """Generate searchable description from skill metadata.

        Args:
            metadata: Skill metadata

        Returns:
            Combined description string
        """
        capabilities = metadata.get("capabilities", [])
        if isinstance(capabilities, list):
            cap_str = " ".join(
                [str(c) if isinstance(c, str) else c.get("name", "") for c in capabilities]
            )
        else:
            cap_str = str(capabilities)

        parts = [
            metadata.get("name", ""),
            metadata.get("description", ""),
            cap_str,
        ]
        return " ".join(filter(None, parts))

    def index_all_skills(self) -> dict[str, Any]:
        """Index all skills in the skills directory.

        Returns:
            Indexing results with count and details
        """
        if not self._initialized:
            self.initialize()

        skills_dir = Path("orchestrator/skills")
        indexed_skills = []
        failed_skills = []

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name == "__pycache__":
                continue

            skill_name = skill_dir.name
            metadata = self._load_skill_metadata(skill_name)

            if not metadata:
                failed_skills.append(skill_name)
                continue

            # Generate searchable description
            description = self._generate_skill_description(metadata)

            # Generate embedding
            if self.model:
                embedding = cast(Any, self.model).encode(description).tolist()
            else:
                continue

            # Create point for Qdrant
            point_id = hash(skill_name) % (10**9)  # Deterministic ID
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "skill_name": skill_name,
                    "yaml_name": metadata.get("name", skill_name),
                    "description": description,
                    "capabilities": metadata.get("capabilities", []),
                    "version": metadata.get("version", "unknown"),
                    "provider": metadata.get("provider", "unknown"),
                },
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            indexed_skills.append(skill_name)

        return {
            "indexed": len(indexed_skills),
            "failed": len(failed_skills),
            "skills": indexed_skills,
            "failed_skills": failed_skills,
            "total_embeddings": len(indexed_skills),
        }

    def search_skills(
        self, query: str, limit: int = 5, threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """Search for skills using semantic similarity.

        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of matching skills with scores
        """
        # Generate embedding for query
        if not self.model:
            return []
        query_embedding = cast(Any, self.model).encode(query).tolist()

        # Search in Qdrant using query_points
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            score_threshold=threshold,
        )

        # Format results
        skills = []
        for result in results.points:
            if result.payload:
                skills.append(
                    {
                        "skill_name": result.payload["skill_name"],
                        "yaml_name": result.payload["yaml_name"],
                        "description": result.payload["description"],
                        "capabilities": result.payload["capabilities"],
                        "score": result.score,
                    }
                )

        return skills

    def find_skill_by_capability(self, capability: str, limit: int = 5) -> list[dict[str, Any]]:
        """Find skills by specific capability.

        Args:
            capability: Capability to search for
            limit: Maximum results

        Returns:
            List of skills with matching capability
        """
        return self.search_skills(f"capability: {capability}", limit=limit)

    def get_skill_info(self, skill_name: str) -> dict[str, Any] | None:
        """Get detailed information about a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill metadata or None
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=100,
        )

        for point in results[0]:
            if point.payload and point.payload["skill_name"] == skill_name:
                return point.payload

        return None

    def list_all_skills(self) -> list[dict[str, Any]]:
        """List all indexed skills.

        Returns:
            List of all skills with metadata
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=100,
        )

        skills = []
        for point in results[0]:
            if point.payload:
                skills.append(
                    {
                        "skill_name": point.payload["skill_name"],
                        "yaml_name": point.payload["yaml_name"],
                        "description": point.payload["description"],
                        "capabilities": point.payload["capabilities"],
                        "version": point.payload["version"],
                    }
                )

        return sorted(skills, key=lambda x: x["skill_name"])

    def export_index(self, filepath: str) -> None:
        """Export indexed skills to JSON file.

        Args:
            filepath: Path to save the export
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=100,
        )

        export_data = {
            "indexed_at": str(Path.cwd()),
            "total_skills": len(results[0]),
            "skills": [point.payload for point in results[0]],
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

    def get_stats(self) -> dict[str, Any]:
        """Get indexing statistics.

        Returns:
            Statistics about the indexed skills
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=100,
        )

        all_capabilities = set()
        for point in results[0]:
            if point.payload:
                caps = point.payload.get("capabilities", [])
                for cap in caps:
                    if isinstance(cap, str):
                        all_capabilities.add(cap)
                    elif isinstance(cap, dict):
                        all_capabilities.add(cap.get("name", str(cap)))

        import os

        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        return {
            "total_skills": len(results[0]),
            "unique_capabilities": len(all_capabilities),
            "capabilities": sorted(all_capabilities),
            "embedding_model": embedding_model,
            "embedding_dimension": self.embedding_dim,
        }


def main() -> None:
    """Main function to demonstrate indexer usage."""
    indexer = SkillIndexer()

    # Index all skills
    print("Indexing skills...")
    result = indexer.index_all_skills()
    print(f"✅ Indexed {result['indexed']} skills")
    if result["failed"]:
        print(f"⚠️ Failed to index {result['failed']} skills")

    # Show stats
    print("\nSkills Index Statistics:")
    stats = indexer.get_stats()
    for key, value in stats.items():
        if key != "capabilities":
            print(f"  {key}: {value}")

    # Example searches
    print("\nExample Searches:")

    queries = [
        "cache LLM responses",
        "batch API calls",
        "optimize performance",
        "manage cost",
    ]

    for query in queries:
        results = indexer.search_skills(query, limit=3)
        print(f"\n  Query: '{query}'")
        for result in results:
            print(f"    - {result['yaml_name']} (score: {result['score']:.2f})")
            print(f"      {result['description'][:60]}...")

    # List all skills
    print("\n\nAll Indexed Skills:")
    all_skills = indexer.list_all_skills()
    for skill in all_skills:
        print(f"  ✓ {skill['yaml_name']:25} - {skill['description'][:50]}...")


if __name__ == "__main__":
    main()
