"""
ToolWeaver Skills System

Standards-based skills architecture following Agent Skills specification (agentskills.io).
Uses existing infrastructure (Qdrant for discovery, Redis for state, memory for context).

Architecture:
  - Skill metadata layer on top of existing modules
  - Semantic discovery via Qdrant embeddings
  - State management via Redis
  - No refactoring of existing code needed

Usage:
    from orchestrator.skills import SkillRegistry, discover_skills

    registry = SkillRegistry()

    # Discover skills semantically
    skills = discover_skills("I need to track API costs")

    # Load and use skill
    skill = registry.load("cost-control")
    skill.track_api_call(agent="agent1", model="gpt-4", tokens=100)
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class SkillCapability:
    """A single capability provided by a skill."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    returns: str | None = None


@dataclass
class SkillMetadata:
    """Metadata following Agent Skills specification."""

    name: str
    version: str
    description: str
    author: str
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    capabilities: list[SkillCapability] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: str = "stable"  # alpha, beta, stable, deprecated
    docs_url: str | None = None
    source_url: str | None = None
    license: str = "Apache-2.0"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillMetadata":
        """Create from dictionary."""
        # Convert capability dicts to SkillCapability objects
        if "capabilities" in data and data["capabilities"]:
            data["capabilities"] = [
                SkillCapability(**cap) if isinstance(cap, dict) else cap
                for cap in data["capabilities"]
            ]
        # Convert date strings to datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class SkillRegistry:
    """
    Registry for ToolWeaver skills.

    Follows Agent Skills specification with:
    - Metadata-based discovery
    - Semantic search via Qdrant (optional)
    - State management via Redis (optional)
    - Lazy loading of implementations

    Skills are wrappers around existing modules - no refactoring needed.
    """

    def __init__(self, skills_dir: Path | None = None):
        """Initialize skill registry.

        Args:
            skills_dir: Directory containing skill definitions (defaults to ./skills)
        """
        self.skills_dir = skills_dir or Path(__file__).parent
        self.skills: dict[str, SkillMetadata] = {}
        self.loaded_skills: dict[str, Any] = {}
        self._discover_skills()

    def _discover_skills(self) -> None:
        """Discover skills by scanning skills directory."""
        if not self.skills_dir.exists():
            return

        for skill_path in self.skills_dir.iterdir():
            if not skill_path.is_dir():
                continue

            # Look for skill.yaml (standard) or SKILL.md (anthropic format)
            yaml_path = skill_path / "skill.yaml"
            md_path = skill_path / "SKILL.md"

            if yaml_path.exists():
                metadata = self._load_yaml_skill(yaml_path)
            elif md_path.exists():
                metadata = self._load_md_skill(md_path)
            else:
                continue

            if metadata:
                self.skills[metadata.name] = metadata

    def _load_yaml_skill(self, path: Path) -> SkillMetadata | None:
        """Load skill from skill.yaml (Agent Skills standard)."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return SkillMetadata.from_dict(data)
        except Exception as e:
            print(f"Error loading skill from {path}: {e}")
            return None

    def _load_md_skill(self, path: Path) -> SkillMetadata | None:
        """Load skill from SKILL.md (Anthropic format with YAML frontmatter)."""
        try:
            with open(path) as f:
                content = f.read()

            # Extract YAML frontmatter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])
            return SkillMetadata.from_dict(frontmatter)
        except Exception as e:
            print(f"Error loading skill from {path}: {e}")
            return None

    def list_skills(
        self, category: str | None = None, tag: str | None = None, status: str | None = None
    ) -> list[str]:
        """List available skills with optional filtering.

        Args:
            category: Filter by category
            tag: Filter by tag
            status: Filter by status (alpha, beta, stable, deprecated)

        Returns:
            List of skill names
        """
        skills = list(self.skills.values())

        if category:
            skills = [s for s in skills if category in s.categories]
        if tag:
            skills = [s for s in skills if tag in s.tags]
        if status:
            skills = [s for s in skills if s.status == status]

        return [s.name for s in skills]

    def get_metadata(self, skill_name: str) -> SkillMetadata | None:
        """Get metadata for a skill.

        Args:
            skill_name: Name of skill

        Returns:
            SkillMetadata or None if not found
        """
        return self.skills.get(skill_name)

    def get_skill_metadata(self, skill_name: str) -> SkillMetadata | None:
        """Alias for get_metadata for backward compatibility."""
        return self.get_metadata(skill_name)

    def load(self, skill_name: str) -> Any | None:
        """Load and return skill implementation.

        Args:
            skill_name: Name of skill to load

        Returns:
            Skill instance or None if not found
        """
        # Return cached if already loaded
        if skill_name in self.loaded_skills:
            return self.loaded_skills[skill_name]

        # Check if skill exists
        metadata = self.get_metadata(skill_name)
        if not metadata:
            return None

        # Dynamically load skill implementation
        try:
            # Import from orchestrator._internal or skills module
            skill_module = __import__(f"orchestrator.skills.{skill_name}", fromlist=["Skill"])
            skill_class = getattr(skill_module, "Skill", None)
            if not skill_class:
                return None

            skill_instance = skill_class()
            self.loaded_skills[skill_name] = skill_instance
            return skill_instance
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(
                f"Could not load implementation for skill {skill_name}: {type(e).__name__}: {e}"
            )
            return None

    def search(self, query: str, limit: int = 5) -> list[SkillMetadata]:
        """Simple text search for skills.

        For semantic search, use SemanticSkillDiscovery with Qdrant.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching skill metadata
        """
        query_lower = query.lower()
        matches = []

        for skill in self.skills.values():
            score = 0

            # Check name
            if query_lower in skill.name.lower():
                score += 10

            # Check description
            if query_lower in skill.description.lower():
                score += 5

            # Check tags
            for tag in skill.tags:
                if query_lower in tag.lower():
                    score += 3

            # Check categories
            for category in skill.categories:
                if query_lower in category.lower():
                    score += 3

            if score > 0:
                matches.append((score, skill))

        # Sort by score and return top results
        matches.sort(reverse=True, key=lambda x: x[0])
        return [skill for _, skill in matches[:limit]]

    def to_claude_format(self) -> list[dict[str, Any]]:
        """Export all skills as Claude SDK tool schema format.

        Returns tool definitions compatible with Claude API:
        https://docs.anthropic.com/claude/reference/tool-use

        Returns:
            List of tool definitions in Claude format
        """
        tools = []

        for skill in self.skills.values():
            for capability in skill.capabilities:
                # Handle parameters that might be dict or string
                params = capability.parameters
                if isinstance(params, str):
                    params = json.loads(params) if params.strip() else {}
                elif not params:
                    params = {}

                tool = {
                    "name": f"{skill.name}_{capability.name}".replace("-", "_"),
                    "description": capability.description or f"{skill.name}: {capability.name}",
                    "input_schema": {
                        "type": "object",
                        "properties": params.get("properties", {}),
                        "required": params.get("required", []),
                    },
                }
                tools.append(tool)

        return tools

    def to_openai_format(self) -> list[dict[str, Any]]:
        """Export all skills as OpenAI function schema format.

        Returns function definitions compatible with OpenAI API:
        https://platform.openai.com/docs/api-reference/chat/create#chat-create-functions

        Returns:
            List of function definitions in OpenAI format
        """
        functions = []

        for skill in self.skills.values():
            for capability in skill.capabilities:
                # Handle parameters that might be dict or string
                params = capability.parameters
                if isinstance(params, str):
                    params = json.loads(params) if params.strip() else {}
                elif not params:
                    params = {}

                function = {
                    "name": f"{skill.name}_{capability.name}".replace("-", "_"),
                    "description": capability.description or f"{skill.name}: {capability.name}",
                    "parameters": {
                        "type": "object",
                        "properties": params.get("properties", {}),
                        "required": params.get("required", []),
                    },
                }
                functions.append(function)

        return functions


# Global registry instance
_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Get global skill registry (singleton)."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def list_skills(**filters: Any) -> list[str]:
    """List available skills with optional filters."""
    return get_registry().list_skills(**filters)


def load_skill(name: str) -> Any | None:
    """Load a skill by name."""
    return get_registry().load(name)


def get_skill_metadata(name: str) -> SkillMetadata | None:
    """Get metadata for a skill."""
    return get_registry().get_metadata(name)


def search_skills(query: str, limit: int = 5) -> list[SkillMetadata]:
    """Search for skills."""
    return get_registry().search(query, limit)


def to_claude_format() -> list[dict[str, Any]]:
    """Export all skills as Claude SDK tool schema format.

    Returns:
        List of tool definitions compatible with Claude API
    """
    return get_registry().to_claude_format()


def to_openai_format() -> list[dict[str, Any]]:
    """Export all skills as OpenAI function schema format.

    Returns:
        List of function definitions compatible with OpenAI API
    """
    return get_registry().to_openai_format()


__all__ = [
    "SkillRegistry",
    "SkillMetadata",
    "SkillCapability",
    "get_registry",
    "list_skills",
    "load_skill",
    "get_skill_metadata",
    "search_skills",
    "to_claude_format",
    "to_openai_format",
]
