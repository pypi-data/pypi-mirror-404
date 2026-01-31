"""
Authentication utilities for MCP adapters.

Supports bearer tokens, API keys, basic auth, and explicit no-auth.
Tokens and credentials are sourced from environment variables to avoid
embedding secrets in config files.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Literal

MCPAuthType = Literal["none", "bearer", "api_key", "basic"]


@dataclass
class MCPAuthConfig:
    """Configuration for MCP adapter authentication."""

    type: MCPAuthType = "none"
    token_env: str | None = None
    header_name: str = "Authorization"
    username_env: str | None = None
    password_env: str | None = None

    def __post_init__(self) -> None:
        if self.type in ("bearer", "api_key") and not self.token_env:
            raise ValueError(f"token_env is required for auth type '{self.type}'")

        if self.type == "basic" and (not self.username_env or not self.password_env):
            raise ValueError("username_env and password_env are required for basic auth")


class MCPAuthManager:
    """Build authentication headers for MCP HTTP/WebSocket adapters."""

    def get_headers(self, config: MCPAuthConfig | None) -> dict[str, str]:
        if config is None or config.type == "none":
            return {}

        if config.type == "bearer":
            token = _require_env(config.token_env)
            return {config.header_name: f"Bearer {token}"}

        if config.type == "api_key":
            token = _require_env(config.token_env)
            return {config.header_name: token}

        if config.type == "basic":
            username = _require_env(config.username_env)
            password = _require_env(config.password_env)
            creds = f"{username}:{password}".encode()
            encoded = base64.b64encode(creds).decode()
            return {config.header_name: f"Basic {encoded}"}

        raise ValueError(f"Unsupported auth type: {config.type}")

    def validate_config(self, config: MCPAuthConfig | None) -> bool:
        if config is None or config.type == "none":
            return True

        if config.type in ("bearer", "api_key"):
            return bool(config.token_env and os.getenv(config.token_env))

        if config.type == "basic":
            return bool(
                config.username_env
                and config.password_env
                and os.getenv(config.username_env)
                and os.getenv(config.password_env)
            )

        return False


def _require_env(name: str | None) -> str:
    if not name:
        raise ValueError("Environment variable name is required")
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Authentication value not found in environment variable '{name}'")
    return value
