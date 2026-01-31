"""
Profile Management - Abstract Base Class

Defines the interface for loading and managing agent profiles.
Profiles contain system prompts, tools, settings, and configuration.

Phase 2: File-based profiles (YAML)
Phase 5: Database profiles, S3 profiles, API profiles
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class ProfileError(Exception):
    """Raised when profile operations fail."""

    pass


class ProfileLoader(ABC):
    """
    Abstract base class for profile loading strategies.

    Profiles define agent behavior, tools, prompts, and settings.
    Different implementations can load from files, databases, or APIs.

    Example:
        loader = get_profile_loader("file")
        profile = loader.load_profile("default")
        print(profile["system_prompt"])
    """

    @abstractmethod
    def load_profile(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """
        Load a profile by name.

        Args:
            name: Profile name/identifier
            **kwargs: Implementation-specific options

        Returns:
            Profile dictionary with keys like:
            - system_prompt: str
            - tools: List[str]
            - settings: Dict[str, Any]
            - metadata: Dict[str, Any]

        Raises:
            ProfileError: If profile not found or invalid
        """
        pass

    @abstractmethod
    def save_profile(self, name: str, profile: dict[str, Any], **kwargs: Any) -> bool:
        """
        Save or update a profile.

        Args:
            name: Profile name/identifier
            profile: Profile data dictionary
            **kwargs: Implementation-specific options

        Returns:
            True if successful, False otherwise

        Raises:
            ProfileError: If save operation fails
        """
        pass

    @abstractmethod
    def delete_profile(self, name: str, **kwargs: Any) -> bool:
        """
        Delete a profile.

        Args:
            name: Profile name/identifier
            **kwargs: Implementation-specific options

        Returns:
            True if deleted, False if not found

        Raises:
            ProfileError: If delete operation fails
        """
        pass

    @abstractmethod
    def list_profiles(self, **kwargs: Any) -> list[str]:
        """
        List all available profile names.

        Args:
            **kwargs: Implementation-specific options (e.g., category filter)

        Returns:
            List of profile names
        """
        pass

    @abstractmethod
    def exists(self, name: str, **kwargs: Any) -> bool:
        """
        Check if a profile exists.

        Args:
            name: Profile name/identifier
            **kwargs: Implementation-specific options

        Returns:
            True if profile exists, False otherwise
        """
        pass

    @abstractmethod
    def validate_profile(self, profile: dict[str, Any], **kwargs: Any) -> bool:
        """
        Validate profile structure and required fields.

        Args:
            profile: Profile data to validate
            **kwargs: Implementation-specific validation options

        Returns:
            True if valid, False otherwise

        Raises:
            ProfileError: If validation fails with details
        """
        pass


def get_profile_loader(loader_type: str = "file", **kwargs: Any) -> ProfileLoader:
    """
    Factory function to get profile loader instance.

    Args:
        loader_type: Type of loader ("file", "database", "s3", "api")
        **kwargs: Loader-specific initialization parameters

    Returns:
        ProfileLoader instance

    Raises:
        ValueError: If loader_type is unknown
        ProfileError: If initialization fails

    Example:
        # File loader (default)
        loader = get_profile_loader("file", profiles_dir="./profiles")

        # Database loader (Phase 5)
        loader = get_profile_loader("database", db_url="postgresql://...")

        # S3 loader (Phase 5)
        loader = get_profile_loader("s3", bucket="my-profiles")
    """
    from .file import FileProfileLoader

    loaders = {
        "file": FileProfileLoader,
    }

    # Phase 5: Add enterprise loaders
    # try:
    #     from .database import DatabaseProfileLoader
    #     loaders["database"] = DatabaseProfileLoader
    # except ImportError:
    #     pass

    # try:
    #     from .s3 import S3ProfileLoader
    #     loaders["s3"] = S3ProfileLoader
    # except ImportError:
    #     pass

    # try:
    #     from .api import APIProfileLoader
    #     loaders["api"] = APIProfileLoader
    # except ImportError:
    #     pass

    loader_class = loaders.get(loader_type)
    if not loader_class:
        available = ", ".join(loaders.keys())
        raise ValueError(f"Unknown loader type: {loader_type}. Available loaders: {available}")

    try:
        return loader_class(**kwargs)
    except Exception as e:
        raise ProfileError(f"Failed to initialize {loader_type} loader: {e}") from e
