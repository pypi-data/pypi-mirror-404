"""
Skill Validation & Marketplace: Validate skills and prepare marketplace listings.

Provides validation of skill structure, metadata, and code quality, plus
marketplace listing generation for skill discovery and distribution.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Single validation issue."""

    level: ValidationLevel
    code: str
    message: str
    field: str | None = None
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "line": self.line,
        }


@dataclass
class ValidationResult:
    """Result of skill validation."""

    skill_name: str
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    score: float = 100.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "valid": self.valid,
            "score": self.score,
            "issues": [i.to_dict() for i in self.issues],
            "timestamp": self.timestamp,
        }


@dataclass
class MarketplaceListing:
    """Marketplace listing for a skill."""

    skill_name: str
    display_name: str
    description: str
    version: str
    author: str
    category: str
    tags: list[str]
    capabilities: list[str]
    requirements: dict[str, str]
    validation_score: float
    downloads: int = 0
    rating: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SkillValidator:
    """Validator for skill structure and metadata."""

    # Required metadata fields
    REQUIRED_FIELDS = ["name", "version", "description"]

    # Recommended metadata fields
    RECOMMENDED_FIELDS = ["author", "category", "capabilities", "parameters"]

    # Version pattern (semver)
    VERSION_PATTERN = r"^\d+\.\d+\.\d+$"

    def __init__(self, skills_dir: str = "orchestrator/skills"):
        """
        Initialize validator.

        Args:
            skills_dir: Directory containing skills
        """
        self.skills_dir = Path(skills_dir)

    def validate_skill(self, skill_name: str) -> ValidationResult:
        """
        Validate a skill comprehensively.

        Args:
            skill_name: Name of skill to validate

        Returns:
            ValidationResult
        """
        issues: list[ValidationIssue] = []

        # Check skill directory exists
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="SKILL_NOT_FOUND",
                    message=f"Skill directory not found: {skill_dir}",
                )
            )
            return ValidationResult(skill_name=skill_name, valid=False, issues=issues)

        # Validate structure
        issues.extend(self._validate_structure(skill_dir, skill_name))

        # Load and validate metadata
        metadata = self._load_metadata(skill_dir, skill_name)
        if metadata:
            issues.extend(self._validate_metadata(metadata))
            issues.extend(self._validate_parameters(metadata.get("parameters", {})))
            issues.extend(self._validate_capabilities(metadata.get("capabilities", [])))
        else:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="METADATA_MISSING",
                    message="Skill metadata file not found",
                )
            )

        # Validate Python code
        issues.extend(self._validate_code(skill_dir, skill_name))

        # Calculate validation score
        score = self._calculate_score(issues)

        # Determine if valid (no errors)
        valid = not any(i.level == ValidationLevel.ERROR for i in issues)

        return ValidationResult(
            skill_name=skill_name,
            valid=valid,
            issues=issues,
            score=score,
        )

    def _validate_structure(
        self,
        skill_dir: Path,
        skill_name: str,
    ) -> list[ValidationIssue]:
        """Validate skill directory structure."""
        issues = []

        # Check for required files
        required_files = [
            f"{skill_name}.yaml",
            f"{skill_name}.py",
        ]

        for filename in required_files:
            file_path = skill_dir / filename
            if not file_path.exists():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        code="FILE_MISSING",
                        message=f"Required file missing: {filename}",
                    )
                )

        # Check for __init__.py
        init_file = skill_dir / "__init__.py"
        if not init_file.exists():
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="INIT_MISSING",
                    message="__init__.py not found (recommended)",
                )
            )

        # Check for README
        readme_files = ["README.md", "readme.md", "README.txt"]
        has_readme = any((skill_dir / f).exists() for f in readme_files)
        if not has_readme:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="README_MISSING",
                    message="README file not found (recommended)",
                )
            )

        return issues

    def _load_metadata(
        self,
        skill_dir: Path,
        skill_name: str,
    ) -> dict[str, Any] | None:
        """Load skill metadata."""
        yaml_path = skill_dir / f"{skill_name}.yaml"

        if not yaml_path.exists():
            return None

        try:
            with open(yaml_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata for {skill_name}: {e}")
            return None

    def _validate_metadata(self, metadata: dict[str, Any]) -> list[ValidationIssue]:
        """Validate skill metadata."""
        issues = []

        # Check required fields
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in metadata or not metadata[field_name]:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        code="FIELD_REQUIRED",
                        message=f"Required field missing or empty: {field_name}",
                        field=field_name,
                    )
                )

        # Check recommended fields
        for field_name in self.RECOMMENDED_FIELDS:
            if field_name not in metadata:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="FIELD_RECOMMENDED",
                        message=f"Recommended field missing: {field_name}",
                        field=field_name,
                    )
                )

        # Validate version format
        version = metadata.get("version", "")
        if version and not re.match(self.VERSION_PATTERN, version):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="VERSION_FORMAT",
                    message=f"Version should follow semver (x.y.z): {version}",
                    field="version",
                )
            )

        # Validate description length
        description = metadata.get("description", "")
        if len(description) < 20:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="DESCRIPTION_TOO_SHORT",
                    message="Description should be at least 20 characters",
                    field="description",
                )
            )
        elif len(description) > 500:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="DESCRIPTION_TOO_LONG",
                    message="Description is very long (>500 chars)",
                    field="description",
                )
            )

        return issues

    def _validate_parameters(
        self,
        parameters: dict[str, Any],
    ) -> list[ValidationIssue]:
        """Validate skill parameters."""
        issues = []

        if not parameters:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="NO_PARAMETERS",
                    message="Skill has no parameters defined",
                )
            )
            return issues

        for param_name, param_def in parameters.items():
            if not isinstance(param_def, dict):
                continue

            # Check for type
            if "type" not in param_def:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="PARAM_NO_TYPE",
                        message=f"Parameter missing type: {param_name}",
                        field=f"parameters.{param_name}",
                    )
                )

            # Check for description
            if "description" not in param_def:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        code="PARAM_NO_DESCRIPTION",
                        message=f"Parameter missing description: {param_name}",
                        field=f"parameters.{param_name}",
                    )
                )

        return issues

    def _validate_capabilities(
        self,
        capabilities: list[Any],
    ) -> list[ValidationIssue]:
        """Validate skill capabilities."""
        issues = []

        if not capabilities:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="NO_CAPABILITIES",
                    message="Skill has no capabilities defined",
                )
            )
            return issues

        if len(capabilities) > 20:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="TOO_MANY_CAPABILITIES",
                    message=f"Skill has {len(capabilities)} capabilities (consider reducing)",
                )
            )

        return issues

    def _validate_code(
        self,
        skill_dir: Path,
        skill_name: str,
    ) -> list[ValidationIssue]:
        """Validate Python code quality."""
        issues: list[ValidationIssue] = []

        code_path = skill_dir / f"{skill_name}.py"
        if not code_path.exists():
            return issues

        try:
            with open(code_path, encoding="utf-8") as f:
                code = f.read()

            # Check for docstring
            if not code.strip().startswith('"""') and not code.strip().startswith("'''"):
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="NO_MODULE_DOCSTRING",
                        message="Module docstring not found",
                    )
                )

            # Check for class definition
            if "class " not in code:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        code="NO_CLASS",
                        message="No class definition found",
                    )
                )

            # Check for execute method
            if "def execute(" not in code:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="NO_EXECUTE_METHOD",
                        message="No execute() method found",
                    )
                )

            # Check code length
            lines = code.split("\n")
            if len(lines) > 1000:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        code="CODE_TOO_LONG",
                        message=f"Code is very long ({len(lines)} lines)",
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="CODE_READ_ERROR",
                    message=f"Failed to read code file: {e}",
                )
            )

        return issues

    def _calculate_score(self, issues: list[ValidationIssue]) -> float:
        """Calculate validation score (0-100)."""
        score = 100.0

        for issue in issues:
            if issue.level == ValidationLevel.ERROR:
                score -= 20.0
            elif issue.level == ValidationLevel.WARNING:
                score -= 5.0
            elif issue.level == ValidationLevel.INFO:
                score -= 1.0

        return max(0.0, score)

    def validate_all_skills(self) -> dict[str, ValidationResult]:
        """
        Validate all skills in directory.

        Returns:
            Dictionary of skill_name -> ValidationResult
        """
        results = {}

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            skill_name = skill_dir.name
            result = self.validate_skill(skill_name)
            results[skill_name] = result

        logger.info(f"Validated {len(results)} skills")
        return results


class MarketplaceManager:
    """Manager for skill marketplace listings."""

    def __init__(
        self,
        skills_dir: str = "orchestrator/skills",
        marketplace_file: str = "orchestrator/skills/marketplace.json",
    ):
        """
        Initialize marketplace manager.

        Args:
            skills_dir: Directory containing skills
            marketplace_file: File to persist marketplace data
        """
        self.skills_dir = Path(skills_dir)
        self.marketplace_file = Path(marketplace_file)
        self.validator = SkillValidator(skills_dir)
        self.listings: dict[str, MarketplaceListing] = {}

        # Load existing listings
        self._load_listings()

    def create_listing(
        self,
        skill_name: str,
        auto_validate: bool = True,
    ) -> MarketplaceListing:
        """
        Create a marketplace listing for a skill.

        Args:
            skill_name: Name of skill
            auto_validate: Whether to validate before creating listing

        Returns:
            Created MarketplaceListing
        """
        # Load skill metadata
        skill_dir = self.skills_dir / skill_name
        yaml_path = skill_dir / f"{skill_name}.yaml"

        if not yaml_path.exists():
            raise ValueError(f"Skill metadata not found: {skill_name}")

        with open(yaml_path, encoding="utf-8") as f:
            metadata = yaml.safe_load(f)

        # Validate if requested
        validation_score = 100.0
        if auto_validate:
            result = self.validator.validate_skill(skill_name)
            validation_score = result.score

            if not result.valid:
                logger.warning(f"Skill {skill_name} has validation errors")

        # Extract capabilities
        capabilities = []
        for cap in metadata.get("capabilities", []):
            if isinstance(cap, dict):
                capabilities.append(cap.get("name", str(cap)))
            else:
                capabilities.append(str(cap))

        # Create listing
        listing = MarketplaceListing(
            skill_name=skill_name,
            display_name=metadata.get("display_name", skill_name.replace("_", " ").title()),
            description=metadata.get("description", ""),
            version=metadata.get("version", "0.1.0"),
            author=metadata.get("author", "Unknown"),
            category=metadata.get("category", "general"),
            tags=metadata.get("tags", []),
            capabilities=capabilities,
            requirements=metadata.get("requirements", {}),
            validation_score=validation_score,
        )

        self.listings[skill_name] = listing
        self._save_listings()

        logger.info(f"Created marketplace listing for {skill_name}")
        return listing

    def get_listing(self, skill_name: str) -> MarketplaceListing | None:
        """
        Get a marketplace listing.

        Args:
            skill_name: Name of skill

        Returns:
            MarketplaceListing or None
        """
        return self.listings.get(skill_name)

    def list_all(
        self,
        category: str | None = None,
        min_score: float = 0.0,
        sort_by: str = "name",
    ) -> list[MarketplaceListing]:
        """
        List all marketplace listings.

        Args:
            category: Filter by category
            min_score: Minimum validation score
            sort_by: Sort field (name, score, downloads, rating)

        Returns:
            List of MarketplaceListings
        """
        listings = list(self.listings.values())

        # Filter by category
        if category:
            listings = [listing for listing in listings if listing.category == category]

        # Filter by score
        listings = [listing for listing in listings if listing.validation_score >= min_score]

        # Sort
        sort_keys = {
            "name": lambda listing: listing.skill_name,
            "score": lambda listing: listing.validation_score,
            "downloads": lambda listing: listing.downloads,
            "rating": lambda listing: listing.rating,
        }

        if sort_by in sort_keys:
            listings.sort(key=sort_keys[sort_by], reverse=(sort_by != "name"))

        return listings

    def search_listings(
        self,
        query: str,
        tags: list[str] | None = None,
    ) -> list[MarketplaceListing]:
        """
        Search marketplace listings.

        Args:
            query: Text query
            tags: Filter by tags

        Returns:
            List of matching listings
        """
        results = list(self.listings.values())

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                listing
                for listing in results
                if (
                    query_lower in listing.skill_name.lower()
                    or query_lower in listing.description.lower()
                    or query_lower in listing.display_name.lower()
                )
            ]

        # Tag filter
        if tags:
            results = [listing for listing in results if any(tag in listing.tags for tag in tags)]

        return results

    def update_listing(
        self,
        skill_name: str,
        **kwargs: Any,
    ) -> MarketplaceListing:
        """
        Update a marketplace listing.

        Args:
            skill_name: Name of skill
            **kwargs: Fields to update

        Returns:
            Updated MarketplaceListing
        """
        listing = self.listings.get(skill_name)
        if not listing:
            raise ValueError(f"Listing not found: {skill_name}")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(listing, key):
                setattr(listing, key, value)

        listing.updated_at = datetime.now().isoformat()
        self._save_listings()

        return listing

    def increment_downloads(self, skill_name: str) -> None:
        """Increment download count for a skill."""
        listing = self.listings.get(skill_name)
        if listing:
            listing.downloads += 1
            self._save_listings()

    def set_rating(self, skill_name: str, rating: float) -> None:
        """
        Set rating for a skill.

        Args:
            skill_name: Name of skill
            rating: Rating (0.0 - 5.0)
        """
        if not 0.0 <= rating <= 5.0:
            raise ValueError("Rating must be between 0.0 and 5.0")

        listing = self.listings.get(skill_name)
        if listing:
            listing.rating = rating
            listing.updated_at = datetime.now().isoformat()
            self._save_listings()

    def create_all_listings(self) -> int:
        """
        Create listings for all skills.

        Returns:
            Number of listings created
        """
        count = 0

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            skill_name = skill_dir.name

            try:
                self.create_listing(skill_name)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to create listing for {skill_name}: {e}")

        logger.info(f"Created {count} marketplace listings")
        return count

    def _load_listings(self) -> None:
        """Load listings from file."""
        if not self.marketplace_file.exists():
            return

        try:
            with open(self.marketplace_file, encoding="utf-8") as f:
                data = json.load(f)

            for listing_data in data.get("listings", []):
                listing = MarketplaceListing(**listing_data)
                self.listings[listing.skill_name] = listing

            logger.info(f"Loaded {len(self.listings)} marketplace listings")

        except Exception as e:
            logger.error(f"Failed to load marketplace listings: {e}")

    def _save_listings(self) -> None:
        """Save listings to file."""
        self.marketplace_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "listings": [listing.to_dict() for listing in self.listings.values()],
            "updated_at": datetime.now().isoformat(),
        }

        try:
            with open(self.marketplace_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved marketplace listings to {self.marketplace_file}")
        except Exception as e:
            logger.error(f"Failed to save marketplace listings: {e}")

    def export_marketplace(self, output_path: str) -> None:
        """
        Export marketplace to JSON.

        Args:
            output_path: Output file path
        """
        data = {
            "marketplace": {
                "total_skills": len(self.listings),
                "categories": list({listing.category for listing in self.listings.values()}),
                "listings": [listing.to_dict() for listing in self.listings.values()],
            },
            "exported_at": datetime.now().isoformat(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported marketplace to {output_path}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get marketplace statistics.

        Returns:
            Statistics dictionary
        """
        if not self.listings:
            return {
                "total_listings": 0,
                "total_downloads": 0,
                "average_score": 0.0,
                "average_rating": 0.0,
            }

        return {
            "total_listings": len(self.listings),
            "total_downloads": sum(listing.downloads for listing in self.listings.values()),
            "average_score": sum(listing.validation_score for listing in self.listings.values())
            / len(self.listings),
            "average_rating": sum(listing.rating for listing in self.listings.values())
            / len(self.listings),
            "categories": len({listing.category for listing in self.listings.values()}),
        }
