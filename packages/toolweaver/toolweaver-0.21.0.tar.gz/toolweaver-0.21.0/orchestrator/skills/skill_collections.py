"""
Skill Collections: Organize skills into groups with tags and categories.

Provides collection management for organizing, discovering, and managing
related skills through tags, categories, and custom collections.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillTag:
    """Tag for categorizing skills."""

    name: str
    category: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SkillCollection:
    """Collection of related skills."""

    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CollectionManager:
    """Manager for skill collections, tags, and categories."""

    # Predefined categories
    CATEGORIES = {
        "optimization": "Performance and cost optimization",
        "caching": "Caching and storage",
        "routing": "Message and request routing",
        "planning": "Task planning and orchestration",
        "execution": "Task execution and management",
        "monitoring": "Monitoring and observability",
        "security": "Security and authentication",
        "integration": "External service integration",
    }

    def __init__(
        self,
        skills_dir: str = "orchestrator/skills",
        collections_file: str = "orchestrator/skills/collections.json",
    ):
        """
        Initialize collection manager.

        Args:
            skills_dir: Directory containing skills
            collections_file: File to persist collections
        """
        self.skills_dir = Path(skills_dir)
        self.collections_file = Path(collections_file)
        self.collections: dict[str, SkillCollection] = {}
        self.tags: dict[str, SkillTag] = {}
        self.skill_tags: dict[str, set[str]] = {}  # skill_name -> set of tags

        # Load existing data
        self._load_collections()
        self._load_skill_tags()

    # ===== Collection Management =====

    def create_collection(
        self,
        name: str,
        description: str,
        skills: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SkillCollection:
        """
        Create a new skill collection.

        Args:
            name: Collection name
            description: Collection description
            skills: Initial skills in collection
            tags: Collection tags
            metadata: Additional metadata

        Returns:
            Created SkillCollection
        """
        if name in self.collections:
            raise ValueError(f"Collection already exists: {name}")

        collection = SkillCollection(
            name=name,
            description=description,
            skills=skills or [],
            tags=tags or [],
            metadata=metadata or {},
        )

        self.collections[name] = collection
        self._save_collections()

        logger.info(f"Created collection: {name}")
        return collection

    def get_collection(self, name: str) -> SkillCollection | None:
        """
        Get a collection by name.

        Args:
            name: Collection name

        Returns:
            SkillCollection or None
        """
        return self.collections.get(name)

    def get_collection_skills(self, name: str) -> list[str]:
        """
        Get skills in a collection by name.

        Args:
            name: Collection name

        Returns:
            List of skill IDs in the collection, or empty list if not found
        """
        collection = self.collections.get(name)
        if collection:
            return collection.skills
        return []

    def list_collections(self) -> list[SkillCollection]:
        """
        List all collections.

        Returns:
            List of SkillCollections
        """
        return list(self.collections.values())

    def update_collection(
        self,
        name: str,
        description: str | None = None,
        skills: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SkillCollection:
        """
        Update an existing collection.

        Args:
            name: Collection name
            description: New description (optional)
            skills: New skills list (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            Updated SkillCollection
        """
        collection = self.collections.get(name)
        if not collection:
            raise ValueError(f"Collection not found: {name}")

        if description is not None:
            collection.description = description
        if skills is not None:
            collection.skills = skills
        if tags is not None:
            collection.tags = tags
        if metadata is not None:
            collection.metadata.update(metadata)

        collection.updated_at = datetime.now().isoformat()
        self._save_collections()

        logger.info(f"Updated collection: {name}")
        return collection

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name

        Returns:
            True if deleted, False if not found
        """
        if name in self.collections:
            del self.collections[name]
            self._save_collections()
            logger.info(f"Deleted collection: {name}")
            return True
        return False

    def add_skill_to_collection(self, collection_name: str, skill_name: str) -> None:
        """
        Add a skill to a collection.

        Args:
            collection_name: Name of collection
            skill_name: Name of skill to add
        """
        collection = self.collections.get(collection_name)
        if not collection:
            raise ValueError(f"Collection not found: {collection_name}")

        if skill_name not in collection.skills:
            collection.skills.append(skill_name)
            collection.updated_at = datetime.now().isoformat()
            self._save_collections()
            logger.info(f"Added {skill_name} to collection {collection_name}")

    def remove_skill_from_collection(
        self,
        collection_name: str,
        skill_name: str,
    ) -> None:
        """
        Remove a skill from a collection.

        Args:
            collection_name: Name of collection
            skill_name: Name of skill to remove
        """
        collection = self.collections.get(collection_name)
        if not collection:
            raise ValueError(f"Collection not found: {collection_name}")

        if skill_name in collection.skills:
            collection.skills.remove(skill_name)
            collection.updated_at = datetime.now().isoformat()
            self._save_collections()
            logger.info(f"Removed {skill_name} from collection {collection_name}")

    # ===== Tag Management =====

    def create_tag(
        self,
        name: str,
        category: str | None = None,
        description: str | None = None,
    ) -> SkillTag:
        """
        Create a new tag.

        Args:
            name: Tag name
            category: Tag category (optional)
            description: Tag description (optional)

        Returns:
            Created SkillTag
        """
        if name in self.tags:
            raise ValueError(f"Tag already exists: {name}")

        tag = SkillTag(name=name, category=category, description=description)
        self.tags[name] = tag
        self._save_collections()

        logger.info(f"Created tag: {name}")
        return tag

    def get_tag(self, name: str) -> SkillTag | None:
        """
        Get a tag by name.

        Args:
            name: Tag name

        Returns:
            SkillTag or None
        """
        return self.tags.get(name)

    def list_tags(self, category: str | None = None) -> list[SkillTag]:
        """
        List all tags, optionally filtered by category.

        Args:
            category: Filter by category (optional)

        Returns:
            List of SkillTags
        """
        tags = list(self.tags.values())
        if category:
            tags = [t for t in tags if t.category == category]
        return tags

    def tag_skill(self, skill_name: str, tag_name: str) -> None:
        """
        Add a tag to a skill.

        Args:
            skill_name: Name of skill
            tag_name: Name of tag
        """
        if skill_name not in self.skill_tags:
            self.skill_tags[skill_name] = set()

        self.skill_tags[skill_name].add(tag_name)
        self._save_collections()
        logger.info(f"Tagged {skill_name} with {tag_name}")

    def untag_skill(self, skill_name: str, tag_name: str) -> None:
        """
        Remove a tag from a skill.

        Args:
            skill_name: Name of skill
            tag_name: Name of tag
        """
        if skill_name in self.skill_tags:
            self.skill_tags[skill_name].discard(tag_name)
            self._save_collections()
            logger.info(f"Removed tag {tag_name} from {skill_name}")

    def get_skill_tags(self, skill_name: str) -> list[str]:
        """
        Get all tags for a skill.

        Args:
            skill_name: Name of skill

        Returns:
            List of tag names
        """
        return list(self.skill_tags.get(skill_name, set()))

    def get_skills_by_tag(self, tag_name: str) -> list[str]:
        """
        Get all skills with a specific tag.

        Args:
            tag_name: Tag name

        Returns:
            List of skill names
        """
        skills = []
        for skill_name, tags in self.skill_tags.items():
            if tag_name in tags:
                skills.append(skill_name)
        return skills

    def get_skills_by_category(self, category: str) -> list[str]:
        """
        Get all skills in a category.

        Args:
            category: Category name

        Returns:
            List of skill names
        """
        # Get tags in this category
        category_tags = [t.name for t in self.tags.values() if t.category == category]

        # Get skills with any of these tags
        skills = set()
        for tag in category_tags:
            skills.update(self.get_skills_by_tag(tag))

        return list(skills)

    # ===== Query and Search =====

    def search_collections(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        skills: list[str] | None = None,
    ) -> list[SkillCollection]:
        """
        Search for collections.

        Args:
            query: Text query to search in name/description
            tags: Filter by tags
            skills: Filter by skills

        Returns:
            List of matching collections
        """
        results = list(self.collections.values())

        # Filter by text query
        if query:
            query_lower = query.lower()
            results = [
                c
                for c in results
                if query_lower in c.name.lower() or query_lower in c.description.lower()
            ]

        # Filter by tags
        if tags:
            results = [c for c in results if any(tag in c.tags for tag in tags)]

        # Filter by skills
        if skills:
            results = [c for c in results if any(skill in c.skills for skill in skills)]

        return results

    def get_collections_for_skill(self, skill_name: str) -> list[SkillCollection]:
        """
        Get all collections containing a skill.

        Args:
            skill_name: Name of skill

        Returns:
            List of collections
        """
        return [c for c in self.collections.values() if skill_name in c.skills]

    def get_related_skills(
        self,
        skill_name: str,
        limit: int = 5,
    ) -> list[str]:
        """
        Get related skills based on shared collections and tags.

        Args:
            skill_name: Name of skill
            limit: Maximum number of results

        Returns:
            List of related skill names
        """
        # Get collections containing this skill
        collections = self.get_collections_for_skill(skill_name)

        # Get all skills in these collections
        related = set()
        for collection in collections:
            related.update(collection.skills)

        # Get skills with shared tags
        skill_tags = self.get_skill_tags(skill_name)
        for tag in skill_tags:
            related.update(self.get_skills_by_tag(tag))

        # Remove the original skill
        related.discard(skill_name)

        return list(related)[:limit]

    # ===== Predefined Collections =====

    def create_default_collections(self) -> None:
        """Create default skill collections based on categories."""
        for category, description in self.CATEGORIES.items():
            collection_name = f"{category}_skills"

            if collection_name not in self.collections:
                self.create_collection(
                    name=collection_name,
                    description=f"{description} skills",
                    tags=[category],
                )
                logger.info(f"Created default collection: {collection_name}")

    def auto_organize_skills(self) -> None:
        """
        Auto-organize skills into collections based on their metadata.

        This analyzes skill metadata and automatically assigns them to
        appropriate collections and tags.
        """
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            yaml_path = skill_dir / f"{skill_dir.name}.yaml"
            if not yaml_path.exists():
                continue

            try:
                with open(yaml_path, encoding="utf-8") as f:
                    metadata = yaml.safe_load(f)

                skill_name = skill_dir.name

                # Extract capabilities as tags
                capabilities = metadata.get("capabilities", [])
                for cap in capabilities:
                    if isinstance(cap, dict):
                        cap_name = cap.get("name", "").lower()
                    else:
                        cap_name = str(cap).lower()

                    if cap_name:
                        # Create tag if doesn't exist
                        if cap_name not in self.tags:
                            self.create_tag(cap_name)

                        # Tag the skill
                        self.tag_skill(skill_name, cap_name)

                # Assign to category-based collections
                for category in self.CATEGORIES:
                    if (
                        category in skill_name
                        or category in metadata.get("description", "").lower()
                    ):
                        collection_name = f"{category}_skills"
                        if collection_name in self.collections:
                            self.add_skill_to_collection(collection_name, skill_name)

            except Exception as e:
                logger.warning(f"Failed to auto-organize {skill_dir.name}: {e}")

    # ===== Persistence =====

    def _load_collections(self) -> None:
        """Load collections from file."""
        if not self.collections_file.exists():
            return

        try:
            with open(self.collections_file, encoding="utf-8") as f:
                data = json.load(f)

            # Load collections
            for coll_data in data.get("collections", []):
                collection = SkillCollection(**coll_data)
                self.collections[collection.name] = collection

            # Load tags
            for tag_data in data.get("tags", []):
                tag = SkillTag(**tag_data)
                self.tags[tag.name] = tag

            # Load skill tags
            skill_tags_data = data.get("skill_tags", {})
            self.skill_tags = {k: set(v) for k, v in skill_tags_data.items()}

            logger.info(f"Loaded {len(self.collections)} collections and {len(self.tags)} tags")

        except Exception as e:
            logger.error(f"Failed to load collections: {e}")

    def _save_collections(self) -> None:
        """Save collections to file."""
        self.collections_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "collections": [c.to_dict() for c in self.collections.values()],
            "tags": [t.to_dict() for t in self.tags.values()],
            "skill_tags": {k: list(v) for k, v in self.skill_tags.items()},
        }

        try:
            with open(self.collections_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved collections to {self.collections_file}")
        except Exception as e:
            logger.error(f"Failed to save collections: {e}")

    def _load_skill_tags(self) -> None:
        """Load tags from individual skill metadata."""
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            yaml_path = skill_dir / f"{skill_dir.name}.yaml"
            if not yaml_path.exists():
                continue

            try:
                with open(yaml_path, encoding="utf-8") as f:
                    metadata = yaml.safe_load(f)

                # Load tags from metadata
                skill_tags = metadata.get("tags", [])
                if skill_tags:
                    skill_name = skill_dir.name
                    if skill_name not in self.skill_tags:
                        self.skill_tags[skill_name] = set()
                    self.skill_tags[skill_name].update(skill_tags)

            except Exception as e:
                logger.warning(f"Failed to load tags for {skill_dir.name}: {e}")

    def export_collections(self, output_path: str) -> None:
        """
        Export collections to JSON file.

        Args:
            output_path: Output file path
        """
        data = {
            "collections": [c.to_dict() for c in self.collections.values()],
            "tags": [t.to_dict() for t in self.tags.values()],
            "skill_tags": {k: list(v) for k, v in self.skill_tags.items()},
            "exported_at": datetime.now().isoformat(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported collections to {output_path}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            Statistics dictionary
        """
        total_skills = len(self.skill_tags)
        tagged_skills = sum(1 for tags in self.skill_tags.values() if tags)

        return {
            "total_collections": len(self.collections),
            "total_tags": len(self.tags),
            "total_skills": total_skills,
            "tagged_skills": tagged_skills,
            "categories": list(self.CATEGORIES.keys()),
            "average_skills_per_collection": (
                sum(len(c.skills) for c in self.collections.values()) / len(self.collections)
                if self.collections
                else 0
            ),
            "average_tags_per_skill": (
                sum(len(tags) for tags in self.skill_tags.values()) / len(self.skill_tags)
                if self.skill_tags
                else 0
            ),
        }
