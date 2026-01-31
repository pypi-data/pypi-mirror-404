"""
Centralized Path Management for Phase -1

Consolidates all hardcoded paths into a single source of truth.
Replaces ~35 hardcoded path literals throughout the codebase.

Usage:
    from orchestrator._internal.paths import get_app_dir, get_cache_dir

    skills_dir = get_app_dir("skills")  # ~/.toolweaver/skills
    cache_dir = get_cache_dir()          # ~/.toolweaver/cache
"""

import os
from pathlib import Path

# Environment variable prefix
_ENV_PREFIX = "TOOLWEAVER_"


class AppPaths:
    """
    Centralized application path management.

    All paths are derived from a single base directory:
    - Default: ~/.toolweaver/
    - Override: Set TOOLWEAVER_APP_DIR environment variable

    Subdirectories:
        skills/               - Skill storage
        cache/                - Cache data
        analytics.db          - Analytics database
        registry_config.json  - Registry configuration
        approvals/            - Team approval queue
        audit_logs/           - Audit trail
        change_tracking/      - Change history
        workflows/            - Workflow definitions
        workspaces/           - Workspace data
        search_cache/         - Search cache
        storage/              - Generic storage (backends)
        profiles/             - Agent profiles
        instruments/          - Agent instruments
    """

    _BASE_DIR: Path | None = None

    @classmethod
    def _get_base_dir(cls) -> Path:
        """Get the base application directory."""
        if cls._BASE_DIR is not None:
            return cls._BASE_DIR

        # Check environment variable first
        env_base = os.getenv(f"{_ENV_PREFIX}APP_DIR")
        if env_base:
            cls._BASE_DIR = Path(env_base)
        else:
            # Default: ~/.toolweaver/
            cls._BASE_DIR = Path.home() / ".toolweaver"

        # Create directory if it doesn't exist
        cls._BASE_DIR.mkdir(parents=True, exist_ok=True)

        return cls._BASE_DIR

    @classmethod
    def get_app_dir(cls, *subdir: str) -> Path:
        """
        Get application directory with optional subdirectory.

        Args:
            *subdir: Subdirectory components (e.g., "skills", "cache")

        Returns:
            Path object

        Examples:
            >>> AppPaths.get_app_dir()
            /home/user/.toolweaver

            >>> AppPaths.get_app_dir("skills")
            /home/user/.toolweaver/skills

            >>> AppPaths.get_app_dir("skills", "custom")
            /home/user/.toolweaver/skills/custom
        """
        base = cls._get_base_dir()
        if subdir:
            path = base.joinpath(*subdir)
            path.mkdir(parents=True, exist_ok=True)
            return path
        return base

    @classmethod
    def get_skills_dir(cls) -> Path:
        """Get skills directory (~/.toolweaver/skills)."""
        return cls.get_app_dir("skills")

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Get cache directory (~/.toolweaver/cache)."""
        return cls.get_app_dir("cache")

    @classmethod
    def get_analytics_db(cls) -> Path:
        """Get analytics database path."""
        return cls.get_app_dir() / "analytics.db"

    @classmethod
    def get_registry_config(cls) -> Path:
        """Get registry configuration path."""
        return cls.get_app_dir() / "registry_config.json"

    @classmethod
    def get_registry_cache_dir(cls) -> Path:
        """Get registry cache directory."""
        return cls.get_app_dir("registry_cache")

    @classmethod
    def get_approvals_dir(cls) -> Path:
        """Get approvals directory for team collaboration."""
        return cls.get_app_dir("approvals")

    @classmethod
    def get_audit_logs_dir(cls) -> Path:
        """Get audit logs directory."""
        return cls.get_app_dir("audit_logs")

    @classmethod
    def get_change_tracking_dir(cls) -> Path:
        """Get change tracking directory."""
        return cls.get_app_dir("change_tracking")

    @classmethod
    def get_workflows_dir(cls) -> Path:
        """Get workflows directory."""
        return cls.get_app_dir("workflows")

    @classmethod
    def get_workspaces_dir(cls) -> Path:
        """Get workspaces directory."""
        return cls.get_app_dir("workspaces")

    @classmethod
    def get_search_cache_dir(cls) -> Path:
        """Get search cache directory."""
        return cls.get_app_dir("cache", "search")

    @classmethod
    def get_storage_dir(cls) -> Path:
        """Get storage directory for backends."""
        return cls.get_app_dir("storage")

    @classmethod
    def get_profiles_dir(cls) -> Path:
        """Get profiles directory for agent profiles."""
        return cls.get_app_dir("profiles")

    @classmethod
    def get_instruments_dir(cls) -> Path:
        """Get instruments directory for agent instruments."""
        return cls.get_app_dir("instruments")

    @classmethod
    def set_base_dir(cls, path: Path) -> None:
        """
        Override the base directory (useful for testing).

        Args:
            path: New base directory path
        """
        cls._BASE_DIR = path.resolve()
        cls._BASE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def reset(cls) -> None:
        """Reset to defaults (useful for testing)."""
        cls._BASE_DIR = None


# Convenience functions at module level
def get_app_dir(*subdir: str) -> Path:
    """Get application directory. Alias for AppPaths.get_app_dir()."""
    return AppPaths.get_app_dir(*subdir)


def get_skills_dir() -> Path:
    """Get skills directory. Alias for AppPaths.get_skills_dir()."""
    return AppPaths.get_skills_dir()


def get_cache_dir() -> Path:
    """Get cache directory. Alias for AppPaths.get_cache_dir()."""
    return AppPaths.get_cache_dir()


def get_analytics_db() -> Path:
    """Get analytics database path."""
    return AppPaths.get_analytics_db()


def get_registry_config() -> Path:
    """Get registry configuration path."""
    return AppPaths.get_registry_config()


def get_registry_cache_dir() -> Path:
    """Get registry cache directory."""
    return AppPaths.get_registry_cache_dir()


def get_approvals_dir() -> Path:
    """Get approvals directory."""
    return AppPaths.get_approvals_dir()


def get_audit_logs_dir() -> Path:
    """Get audit logs directory."""
    return AppPaths.get_audit_logs_dir()


def get_change_tracking_dir() -> Path:
    """Get change tracking directory."""
    return AppPaths.get_change_tracking_dir()


def get_workflows_dir() -> Path:
    """Get workflows directory."""
    return AppPaths.get_workflows_dir()


def get_workspaces_dir() -> Path:
    """Get workspaces directory."""
    return AppPaths.get_workspaces_dir()


def get_search_cache_dir() -> Path:
    """Get search cache directory."""
    return AppPaths.get_search_cache_dir()


def get_storage_dir() -> Path:
    """Get storage directory."""
    return AppPaths.get_storage_dir()


def get_profiles_dir() -> Path:
    """Get profiles directory."""
    return AppPaths.get_profiles_dir()


def get_instruments_dir() -> Path:
    """Get instruments directory."""
    return AppPaths.get_instruments_dir()
