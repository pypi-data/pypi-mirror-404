"""
File-Based Profile Loader

Loads agent profiles from YAML files in a directory.
Default implementation with zero dependencies (uses PyYAML from project deps).
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from .base import ProfileError, ProfileLoader

logger = logging.getLogger(__name__)


class FileProfileLoader(ProfileLoader):
    """
    Load profiles from YAML files.

    Directory structure:
        profiles/
            default.yaml
            researcher.yaml
            coder.yaml

    Profile format (YAML):
        name: "Default Agent"
        system_prompt: "You are a helpful assistant..."
        tools: ["search", "calculator"]
        settings:
            temperature: 0.7
            max_tokens: 2000

    Example:
        loader = FileProfileLoader(profiles_dir="./profiles")
        profile = loader.load_profile("default")
    """

    def __init__(self, profiles_dir: str = "./profiles") -> None:
        """
        Initialize file-based profile loader.

        Args:
            profiles_dir: Directory containing profile YAML files
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FileProfileLoader at: {self.profiles_dir}")

    def _get_profile_path(self, name: str) -> Path:
        """Get file path for profile name."""
        safe_name = name.replace("/", "_").replace("\\", "_")
        return self.profiles_dir / f"{safe_name}.yaml"

    def load_profile(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Load profile from YAML file."""
        try:
            profile_path = self._get_profile_path(name)
            if not profile_path.exists():
                raise ProfileError(f"Profile not found: {name}")

            with open(profile_path, encoding="utf-8") as f:
                profile = yaml.safe_load(f)

            if not isinstance(profile, dict):
                raise ProfileError(f"Invalid profile format: {name}")

            logger.debug(f"Loaded profile: {name}")
            return profile

        except yaml.YAMLError as e:
            raise ProfileError(f"Failed to parse profile {name}: {e}") from None
        except OSError as e:
            raise ProfileError(f"Failed to read profile {name}: {e}") from None

    def save_profile(self, name: str, profile: dict[str, Any], **kwargs: Any) -> bool:
        """Save profile to YAML file."""
        try:
            if not self.validate_profile(profile):
                raise ProfileError(f"Invalid profile structure: {name}")

            profile_path = self._get_profile_path(name)
            with open(profile_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(profile, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved profile: {name}")
            return True

        except (OSError, yaml.YAMLError) as e:
            raise ProfileError(f"Failed to save profile {name}: {e}") from None

    def delete_profile(self, name: str, **kwargs: Any) -> bool:
        """Delete profile YAML file."""
        try:
            profile_path = self._get_profile_path(name)
            if profile_path.exists():
                profile_path.unlink()
                logger.info(f"Deleted profile: {name}")
                return True
            return False
        except OSError as e:
            raise ProfileError(f"Failed to delete profile {name}: {e}") from None

    def list_profiles(self, **kwargs: Any) -> list[str]:
        """List all profile names (YAML files without extension)."""
        profiles = []
        for path in self.profiles_dir.glob("*.yaml"):
            profiles.append(path.stem)
        return sorted(profiles)

    def exists(self, name: str, **kwargs: Any) -> bool:
        """Check if profile YAML file exists."""
        return self._get_profile_path(name).exists()

    def validate_profile(self, profile: dict[str, Any], **kwargs: Any) -> bool:
        """
        Validate profile has minimum required structure.

        Required keys: None (all optional)
        Recommended keys: system_prompt, tools, settings
        """
        if not isinstance(profile, dict):
            raise ProfileError("Profile must be a dictionary")

        # All fields optional, but warn if empty
        if not profile:
            logger.warning("Profile is empty")

        # Validate types if present
        if "tools" in profile and not isinstance(profile["tools"], list):
            raise ProfileError("Profile 'tools' must be a list")

        if "settings" in profile and not isinstance(profile["settings"], dict):
            raise ProfileError("Profile 'settings' must be a dictionary")

        return True

    def __repr__(self) -> str:
        count = len(list(self.profiles_dir.glob("*.yaml")))
        return f"FileProfileLoader(dir={self.profiles_dir}, profiles={count})"
