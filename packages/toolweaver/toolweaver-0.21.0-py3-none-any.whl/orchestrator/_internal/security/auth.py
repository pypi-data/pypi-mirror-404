"""
Security Authentication Module (Phase 9)
"""
import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .rbac import UserRole

logger = logging.getLogger(__name__)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_valid_api_keys() -> set[str]:
    """Retrieve valid API keys from environment or config."""
    # Supports comma-separated keys in TOOLWEAVER_API_KEYS
    keys_str = os.getenv("TOOLWEAVER_API_KEYS", "")
    if not keys_str:
        # Fallback to single key
        key = os.getenv("TOOLWEAVER_API_KEY")
        return {key} if key else set()

    return {k.strip() for k in keys_str.split(",") if k.strip()}

async def verify_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """
    Validate API Key.

    If TOOLWEAVER_API_KEY(S) is not set, authentication is disabled (warning logged).
    """
    valid_keys = get_valid_api_keys()

    # If no keys configured, we assume auth is disabled/dev mode
    if not valid_keys:
        if os.getenv("TOOLWEAVER_AUTH_DISABLED", "false").lower() == "true":
             # Dev mode: assume admin
             return "dev-admin"

        logger.warning("No API keys configured but auth is enabled. Rejecting request.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server configuration error: No API keys defined",
        )

    if not api_key_header or api_key_header not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    return api_key_header

async def get_current_user_role(
    api_key: str = Security(verify_api_key)
) -> UserRole:
    """
    Determine role from API Key.
    Convention: Keys starting with 'admin-' get ADMIN role.
    """
    if api_key.startswith("admin-") or api_key == "dev-admin":
        return UserRole.ADMIN
    return UserRole.USER
