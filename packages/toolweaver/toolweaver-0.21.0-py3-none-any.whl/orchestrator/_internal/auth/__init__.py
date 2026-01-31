"""
Authentication Provider Package (DEPRECATED - use _internal.backends.auth).

Provides pluggable authentication providers.

Re-exports from new location for backwards compatibility.
"""

from orchestrator._internal.backends.auth.base import AuthError, AuthProvider, get_auth_provider
from orchestrator._internal.backends.auth.none import NoAuthProvider

__all__ = [
    "AuthProvider",
    "AuthError",
    "get_auth_provider",
    "NoAuthProvider",
]
