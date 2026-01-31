"""
Profile Management Package (DEPRECATED - use _internal.backends.profiles).

Provides pluggable profile loaders for agent configuration.

Re-exports from new location for backwards compatibility.
"""

from orchestrator._internal.backends.profiles.base import (
    ProfileError,
    ProfileLoader,
    get_profile_loader,
)
from orchestrator._internal.backends.profiles.file import FileProfileLoader

__all__ = [
    "ProfileLoader",
    "ProfileError",
    "get_profile_loader",
    "FileProfileLoader",
]
