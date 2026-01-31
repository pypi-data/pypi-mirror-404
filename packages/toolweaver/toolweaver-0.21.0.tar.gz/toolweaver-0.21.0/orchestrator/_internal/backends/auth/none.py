"""
No Authentication Provider

Passthrough authentication that accepts everything.
Default implementation for development/single-user deployments.
"""

import logging
from typing import Any

from .base import AuthProvider

logger = logging.getLogger(__name__)


class NoAuthProvider(AuthProvider):
    """
    No-op authentication provider.

    All operations succeed without validation.
    Perfect for development, testing, and single-user deployments.

    Example:
        auth = NoAuthProvider()
        token = auth.authenticate({"user": "anyone"})
        assert auth.validate_token(token)  # Always True
    """

    def __init__(self) -> None:
        """Initialize no-auth provider."""
        logger.info("Initialized NoAuthProvider (authentication disabled)")

    def authenticate(self, credentials: dict[str, Any], **kwargs: Any) -> str | None:
        """
        Accept any credentials, return dummy token.

        Args:
            credentials: Any credentials (ignored)

        Returns:
            Dummy token string
        """
        logger.debug("NoAuth: authenticate called (always succeeds)")
        return "no-auth-token"

    def validate_token(self, token: str, **kwargs: Any) -> bool:
        """
        Accept any token as valid.

        Args:
            token: Any token (ignored)

        Returns:
            Always True
        """
        logger.debug("NoAuth: validate_token called (always valid)")
        return True

    def refresh_token(self, token: str, **kwargs: Any) -> str | None:
        """
        Return same token (no refresh needed).

        Args:
            token: Any token

        Returns:
            Same token
        """
        logger.debug("NoAuth: refresh_token called (returns same token)")
        return token

    def revoke_token(self, token: str, **kwargs: Any) -> bool:
        """
        Pretend to revoke token.

        Args:
            token: Any token (ignored)

        Returns:
            Always True
        """
        logger.debug("NoAuth: revoke_token called (no-op)")
        return True

    def __repr__(self) -> str:
        return "NoAuthProvider(disabled)"
