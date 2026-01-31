"""
API Authentication Middleware for Skills Dashboard

Provides API key validation for secure access to the Skills API.
Supports:
- X-API-Key header validation
- Public/private endpoint lists
- Audit logging
- Configurable API keys via .env

Configuration (.env):
- SKILLS_API_KEYS: Comma-separated list of valid API keys (demo-key-12345,prod-key-xyz)
- AUDIT_LOG_ENABLED: true/false (default: true)
- AUDIT_LOG_PATH: Path to audit log file (default: ~/.toolweaver/audit.log)
"""

import logging
import os
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Validates API keys for secure endpoint access."""

    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/api/health",
        "/api/system/info",
    }

    # Public search endpoints (can optionally require auth)
    READONLY_ENDPOINTS = {
        "/api/skills",
        "/api/metrics",
        "/api/collections",
        "/api/marketplace",
        "/api/search",
        "/api/capabilities/search",
    }

    def __init__(self) -> None:
        """Initialize validator with configuration from .env."""
        # Load valid API keys from environment
        api_keys_str = os.getenv("SKILLS_API_KEYS", "")
        self.valid_keys = {key.strip() for key in api_keys_str.split(",") if key.strip()}

        # If no keys configured, add default for development
        if not self.valid_keys:
            self.valid_keys.add("demo-key-12345")
            logger.warning(
                "No SKILLS_API_KEYS configured in .env - using default demo-key-12345. "
                "Set SKILLS_API_KEYS=key1,key2,key3 in production."
            )

        # Audit logging configuration
        self.audit_enabled = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
        audit_path = os.getenv("AUDIT_LOG_PATH", "~/.toolweaver/audit.log")
        self.audit_log_path = Path(audit_path).expanduser()

        # Create audit log directory if needed
        if self.audit_enabled:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def validate_key(self, api_key: str | None) -> bool:
        """Check if API key is valid."""
        if not api_key:
            return False
        return api_key in self.valid_keys

    def is_public_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint is public (doesn't require auth)."""
        # Health/system endpoints always public
        if path in self.PUBLIC_ENDPOINTS:
            return True

        # GET requests to readonly endpoints are public
        if method == "GET" and path.startswith(
            ("/api/skills", "/api/metrics", "/api/collections", "/api/search")
        ):
            return True

        return False

    def is_readonly_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint is read-only (GET methods)."""
        return method == "GET"

    def log_request(self, method: str, path: str, api_key: str, status: str, message: str = "") -> None:
        """Log API request to audit trail."""
        if not self.audit_enabled:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        key_last4 = api_key[-4:] if api_key else "none"
        log_entry = f"{timestamp} | {status:15s} | {method:6s} {path:40s} | Key: ...{key_last4} | {message}\n"

        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Global validator instance
_validator: APIKeyValidator | None = None


def get_validator() -> APIKeyValidator:
    """Get or create global API key validator."""
    global _validator
    if _validator is None:
        _validator = APIKeyValidator()
    return _validator


def require_api_key(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require API key for endpoint.

    Usage:
        @app.route('/api/skills/<id>/execute', methods=['POST'])
        @require_api_key
        def execute_skill(skill_id):
            ...
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        from flask import request

        validator = get_validator()

        # Check if endpoint is public
        if validator.is_public_endpoint(request.path, request.method):
            return f(*args, **kwargs)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        # Validate API key
        if not api_key:
            validator.log_request(request.method, request.path, "", "REJECTED", "Missing API key")
            return {"error": "Missing X-API-Key header"}, 401

        if not validator.validate_key(api_key):
            validator.log_request(
                request.method, request.path, api_key, "REJECTED", "Invalid API key"
            )
            return {"error": "Invalid API key"}, 401

        # Valid key - log and proceed
        validator.log_request(request.method, request.path, api_key, "ALLOWED")

        return f(*args, **kwargs)

    return decorated_function


def require_api_key_for_writes(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require API key only for write operations (POST/PUT/DELETE).
    Read operations (GET) are allowed without key.

    Usage:
        @app.route('/api/skills', methods=['GET', 'POST'])
        @require_api_key_for_writes
        def skill_operations():
            ...
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        from flask import request

        validator = get_validator()

        # GET requests don't need auth
        if request.method == "GET":
            return f(*args, **kwargs)

        # Check if endpoint is public
        if validator.is_public_endpoint(request.path, request.method):
            return f(*args, **kwargs)

        # Write operations need API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            validator.log_request(
                request.method, request.path, "", "REJECTED", "Missing API key for write"
            )
            return {"error": "Missing X-API-Key header for write operations"}, 401

        if not validator.validate_key(api_key):
            validator.log_request(
                request.method, request.path, api_key, "REJECTED", "Invalid API key for write"
            )
            return {"error": "Invalid API key"}, 401

        # Valid key - log and proceed
        validator.log_request(request.method, request.path, api_key, "ALLOWED", "Write operation")

        return f(*args, **kwargs)

    return decorated_function
