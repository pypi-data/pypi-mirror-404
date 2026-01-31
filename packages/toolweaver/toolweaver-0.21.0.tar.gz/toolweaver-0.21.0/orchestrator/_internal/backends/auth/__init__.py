"""Authentication Provider Implementations

Abstract: AuthProvider (base.py)
Implementations:
- NoAuthProvider - No authentication (default for local dev)

Phase 1+: JWT, OAuth2, LDAP, SAML, API Key, etc.
"""

from orchestrator._internal.backends.auth.base import AuthProvider
from orchestrator._internal.backends.auth.none import NoAuthProvider

__all__ = ["AuthProvider", "NoAuthProvider"]
