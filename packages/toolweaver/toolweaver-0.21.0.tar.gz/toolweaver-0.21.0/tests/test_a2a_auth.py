"""
Tests for authentication configuration and management.
"""

from typing import Any

import pytest

from orchestrator._internal.infra.a2a_auth import (
    ANTHROPIC_AUTH,
    AZURE_AUTH,
    GITHUB_AUTH,
    OPENAI_AUTH,
    AuthConfig,
    AuthManager,
)


class TestAuthConfig:
    """Test AuthConfig dataclass."""

    def test_bearer_token_config(self) -> None:
        """Test bearer token configuration."""
        config = AuthConfig(type="bearer", token_env="MY_TOKEN")

        assert config.type == "bearer"
        assert config.token_env == "MY_TOKEN"
        assert config.header_name == "Authorization"  # default

    def test_api_key_config(self) -> None:
        """Test API key configuration."""
        config = AuthConfig(type="api_key", token_env="MY_API_KEY", header_name="X-API-Key")

        assert config.type == "api_key"
        assert config.token_env == "MY_API_KEY"
        assert config.header_name == "X-API-Key"

    def test_no_auth_config(self) -> None:
        """Test configuration without authentication."""
        config = AuthConfig(type="none")

        assert config.type == "none"
        assert config.token_env is None

    def test_missing_token_env_validation(self) -> None:
        """Test that bearer/api_key without token_env raises error."""
        with pytest.raises(ValueError, match="token_env is required"):
            AuthConfig(type="bearer")

        with pytest.raises(ValueError, match="token_env is required"):
            AuthConfig(type="api_key")


class TestAuthManager:
    """Test AuthManager header generation."""

    def test_bearer_token_headers(self, monkeypatch: Any) -> None:
        """Test bearer token header generation."""
        monkeypatch.setenv("TEST_TOKEN", "sk-abc123")

        config = AuthConfig(type="bearer", token_env="TEST_TOKEN")
        manager = AuthManager()
        headers = manager.get_headers(config)

        assert headers == {"Authorization": "Bearer sk-abc123"}

    def test_api_key_headers(self, monkeypatch: Any) -> None:
        """Test API key header generation."""
        monkeypatch.setenv("TEST_KEY", "my-secret-key")

        config = AuthConfig(type="api_key", token_env="TEST_KEY", header_name="X-API-Key")
        manager = AuthManager()
        headers = manager.get_headers(config)

        assert headers == {"X-API-Key": "my-secret-key"}

    def test_no_auth_headers(self) -> None:
        """Test that 'none' auth returns empty headers."""
        config = AuthConfig(type="none")
        manager = AuthManager()
        headers = manager.get_headers(config)

        assert headers == {}

    def test_missing_token_error(self) -> None:
        """Test error when token not in environment."""
        config = AuthConfig(type="bearer", token_env="NONEXISTENT_TOKEN")
        manager = AuthManager()

        with pytest.raises(ValueError, match="not found in environment"):
            manager.get_headers(config)

    def test_validate_config_success(self, monkeypatch: Any) -> None:
        """Test successful config validation."""
        monkeypatch.setenv("VALID_TOKEN", "token123")

        config = AuthConfig(type="bearer", token_env="VALID_TOKEN")
        manager = AuthManager()

        assert manager.validate_config(config) is True

    def test_validate_config_missing_token(self) -> None:
        """Test config validation fails with missing token."""
        config = AuthConfig(type="bearer", token_env="MISSING_TOKEN")
        manager = AuthManager()

        assert manager.validate_config(config) is False

    def test_validate_config_no_auth(self) -> None:
        """Test that 'none' auth always validates."""
        config = AuthConfig(type="none")
        manager = AuthManager()

        assert manager.validate_config(config) is True


class TestPredefinedConfigs:
    """Test predefined service configurations."""

    def test_openai_config(self) -> None:
        """Test OpenAI predefined configuration."""
        assert OPENAI_AUTH.type == "bearer"
        assert OPENAI_AUTH.token_env == "OPENAI_API_KEY"
        assert OPENAI_AUTH.header_name == "Authorization"

    def test_anthropic_config(self) -> None:
        """Test Anthropic predefined configuration."""
        assert ANTHROPIC_AUTH.type == "api_key"
        assert ANTHROPIC_AUTH.token_env == "ANTHROPIC_API_KEY"
        assert ANTHROPIC_AUTH.header_name == "x-api-key"

    def test_github_config(self) -> None:
        """Test GitHub predefined configuration."""
        assert GITHUB_AUTH.type == "bearer"
        assert GITHUB_AUTH.token_env == "GITHUB_TOKEN"
        assert GITHUB_AUTH.header_name == "Authorization"

    def test_azure_config(self) -> None:
        """Test Azure predefined configuration."""
        assert AZURE_AUTH.type == "api_key"
        assert AZURE_AUTH.token_env == "AZURE_API_KEY"
        assert AZURE_AUTH.header_name == "api-key"

    def test_predefined_configs_usage(self, monkeypatch: Any) -> None:
        """Test using predefined configs with AuthManager."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")

        manager = AuthManager()
        headers = manager.get_headers(OPENAI_AUTH)

        assert headers == {"Authorization": "Bearer sk-test123"}


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_token_value(self, monkeypatch: Any) -> None:
        """Test that empty string token is treated as missing."""
        monkeypatch.setenv("EMPTY_TOKEN", "")

        config = AuthConfig(type="bearer", token_env="EMPTY_TOKEN")
        manager = AuthManager()

        with pytest.raises(ValueError, match="not found in environment"):
            manager.get_headers(config)

    def test_whitespace_token(self, monkeypatch: Any) -> None:
        """Test that whitespace-only token is accepted (but not ideal)."""
        monkeypatch.setenv("WHITESPACE_TOKEN", "   ")

        config = AuthConfig(type="bearer", token_env="WHITESPACE_TOKEN")
        manager = AuthManager()
        headers = manager.get_headers(config)

        # Should accept it (validation is caller's responsibility)
        assert headers == {"Authorization": "Bearer    "}

    def test_custom_header_name(self, monkeypatch: Any) -> None:
        """Test custom header name."""
        monkeypatch.setenv("CUSTOM_TOKEN", "token123")

        config = AuthConfig(type="bearer", token_env="CUSTOM_TOKEN", header_name="X-Custom-Auth")
        manager = AuthManager()
        headers = manager.get_headers(config)

        assert headers == {"X-Custom-Auth": "Bearer token123"}
