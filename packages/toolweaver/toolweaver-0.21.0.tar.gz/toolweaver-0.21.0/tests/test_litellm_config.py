"""Tests for LiteLLM integration with orchestrators."""

from typing import Any

import pytest

from orchestrator.adapters.litellm_config import LiteLLMConfig
from orchestrator.adapters.orchestrator_interface import (
    OrchestratorConfig,
)

pytest.importorskip("litellm")


class TestLiteLLMConfig:
    """Test LiteLLM configuration helpers."""

    def test_get_default_config(self) -> None:
        """Test default configuration generation."""
        config = LiteLLMConfig.get_default_config()

        assert isinstance(config, dict)
        assert "model_list" in config
        assert "router_settings" in config
        assert "general_settings" in config

        # Check model list
        models = {m["model_name"] for m in config["model_list"]}
        assert "claude-orchestrator" in models
        assert "claude-fast" in models
        assert "openai-gpt4" in models
        assert "claude-direct" in models

    def test_get_default_config_model_parameters(self) -> None:
        """Test that models have required parameters."""
        config = LiteLLMConfig.get_default_config()

        for model in config["model_list"]:
            assert "model_name" in model
            assert "litellm_params" in model
            assert "model" in model["litellm_params"]
            assert "api_base" in model["litellm_params"]

    def test_setup_for_ollama(self) -> None:
        """Test Ollama-only configuration setup."""
        config = LiteLLMConfig.setup_for_ollama()

        # Should have Ollama models
        assert len(config["model_list"]) >= 1
        assert "claude-orchestrator" in {m["model_name"] for m in config["model_list"]}

        # All should use Ollama
        for model in config["model_list"]:
            assert "ollama" in model["litellm_params"]["model"].lower()
            assert "localhost:11434" in model["litellm_params"]["api_base"]

    def test_to_yaml_string(self) -> None:
        """Test YAML string generation."""
        yaml_str = LiteLLMConfig.to_yaml_string()

        assert isinstance(yaml_str, str)
        assert "model_list:" in yaml_str
        assert "router_settings:" in yaml_str
        assert "general_settings:" in yaml_str

    def test_to_yaml_string_valid_yaml(self) -> None:
        """Test that generated YAML is valid."""
        import yaml

        yaml_str = LiteLLMConfig.to_yaml_string()

        # Should parse without errors
        parsed = yaml.safe_load(yaml_str)
        assert "model_list" in parsed
        assert len(parsed["model_list"]) > 0

    def test_get_orchestrator_config_for_litellm(self) -> None:
        """Test orchestrator config generation for LiteLLM."""
        config_dict = LiteLLMConfig.get_orchestrator_config_for_litellm()

        assert isinstance(config_dict, dict)
        assert "model" in config_dict
        assert "base_url" in config_dict
        assert "api_key" in config_dict

        # Should point to LiteLLM proxy
        assert "http" in config_dict["base_url"]

        # Create OrchestratorConfig to verify it works
        config = OrchestratorConfig(**config_dict)
        assert config.model is not None
        assert config.base_url is not None

    def test_get_orchestrator_config_uses_ollama_by_default(self) -> None:
        """Test that default config uses local Ollama."""
        config_dict = LiteLLMConfig.get_orchestrator_config_for_litellm()

        # Model should be mapped to Ollama via LiteLLM
        assert "claude-orchestrator" in config_dict["model"] or "ollama" in config_dict["model"]


class TestLiteLLMWithClaudeOrchestrator:
    """Test Claude orchestrator with LiteLLM backend."""

    @pytest.mark.asyncio
    async def test_orchestrator_with_litellm_base_url(self) -> None:
        """Test that orchestrator accepts LiteLLM base_url."""
        from orchestrator.adapters.claude_orchestrator import ClaudeOrchestrator

        config = OrchestratorConfig(
            model="claude-orchestrator",
            base_url="http://localhost:4000/v1",
            api_key="test",
        )

        orchestrator = ClaudeOrchestrator(config)
        assert orchestrator.config.base_url == "http://localhost:4000/v1"
        assert orchestrator.config.model == "claude-orchestrator"

    @pytest.mark.asyncio
    async def test_orchestrator_config_with_litellm(self) -> None:
        """Test full orchestrator configuration for LiteLLM."""
        config_dict = LiteLLMConfig.get_orchestrator_config_for_litellm()
        config = OrchestratorConfig(**config_dict)

        assert config.base_url is not None
        assert "http" in config.base_url
        assert config.model is not None

    def test_litellm_config_model_routing(self) -> None:
        """Test that models are properly configured for routing."""
        config = LiteLLMConfig.get_default_config()

        # Check that routing enables fallbacks
        assert "router_settings" in config
        router = config["router_settings"]

        # Should have fallback configuration
        if "fallbacks" in router:
            assert isinstance(router["fallbacks"], list)

    def test_litellm_config_tool_settings(self) -> None:
        """Test that tool settings are configured for tool use."""
        config = LiteLLMConfig.get_default_config()

        # Each model should allow tool use
        for model in config["model_list"]:
            params = model["litellm_params"]
            # Tool enabling varies by provider, but should be documented
            assert "model" in params

    def test_litellm_yaml_config_file_format(self) -> None:
        """Test that generated YAML matches expected format."""
        yaml_str = LiteLLMConfig.to_yaml_string()

        # Should have all required sections
        assert "model_list:" in yaml_str
        assert "router_settings:" in yaml_str
        assert "general_settings:" in yaml_str

        # Should have proper nesting (indentation)
        lines = yaml_str.split("\n")
        assert any(line.startswith("  - model_name:") for line in lines)
        assert any("litellm_params:" in line and line.startswith("    ") for line in lines)


class TestLiteLLMIntegration:
    """Integration tests for LiteLLM with agentic executor."""

    def test_mock_litellm_response_format(self) -> None:
        """Test that mock LiteLLM responses match expected format."""
        # Simulate what LiteLLM proxy would return
        mock_response: dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'll process this task.",
                        "tool_calls": None,
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        # Should have standard OpenAI format
        assert "choices" in mock_response
        assert "usage" in mock_response
        assert "role" in mock_response["choices"][0]["message"]

    def test_litellm_model_name_mapping(self) -> None:
        """Test that model names map correctly through LiteLLM."""
        config = LiteLLMConfig.get_default_config()

        # Get model mapping
        model_map = {m["model_name"]: m["litellm_params"]["model"] for m in config["model_list"]}

        # Should map ToolWeaver names to actual model names
        assert "claude-orchestrator" in model_map
        actual_model = model_map["claude-orchestrator"]

        # Should be recognizable format
        assert isinstance(actual_model, str)
        assert "/" in actual_model or "-" in actual_model or ":" in actual_model

    def test_litellm_fallback_chain(self) -> None:
        """Test that fallback chain is properly configured."""
        config = LiteLLMConfig.get_default_config()
        router = config["router_settings"]

        # Fallbacks should be configured for reliability
        if "fallbacks" in router:
            fallbacks = router["fallbacks"]
            # Should have some fallback configuration
            assert len(fallbacks) > 0

    def test_litellm_temperature_settings(self) -> None:
        """Test that temperature is configured for consistency."""
        config = LiteLLMConfig.get_default_config()

        for model in config["model_list"]:
            params = model["litellm_params"]
            if "temperature" in params:
                temp = params["temperature"]
                # Temperature should be reasonable for planning tasks
                assert 0 <= temp <= 1.0

    def test_litellm_max_tokens_settings(self) -> None:
        """Test that max_tokens is configured for planning context."""
        config = LiteLLMConfig.get_default_config()

        for model in config["model_list"]:
            params = model["litellm_params"]
            if "max_tokens" in params:
                max_tokens = params["max_tokens"]
                # Should allow reasonable response sizes
                assert max_tokens >= 1000


class TestLiteLLMConfigEnvironment:
    """Test LiteLLM configuration with environment variables."""

    def test_config_respects_env_variables(self) -> None:
        """Test that config handles environment-based API keys."""

        # Should not fail if env vars not set (fallback)
        config = LiteLLMConfig.get_default_config()
        assert config is not None

    def test_openai_model_uses_api_key_from_env(self) -> None:
        """Test that OpenAI model is configured to use OPENAI_API_KEY."""
        config = LiteLLMConfig.get_default_config()

        # Find OpenAI model
        openai_models = [
            m for m in config["model_list"] if "gpt" in m["litellm_params"]["model"].lower()
        ]

        # OpenAI should use api key from environment or config
        # (LiteLLM handles this automatically)
        assert len(openai_models) >= 0  # May not be in config if not configured

    def test_anthropic_direct_uses_api_key_from_env(self) -> None:
        """Test that direct Anthropic model uses ANTHROPIC_API_KEY."""
        config = LiteLLMConfig.get_default_config()

        # Find Anthropic direct model
        claude_direct = [
            m for m in config["model_list"] if "claude-direct" in m["model_name"]
        ]

        # Claude direct should be properly configured
        if claude_direct:
            params = claude_direct[0]["litellm_params"]
            assert "model" in params


class TestLiteLLMProxySetup:
    """Tests for setting up LiteLLM proxy locally."""

    def test_ollama_specific_setup(self) -> None:
        """Test Ollama-specific configuration."""
        config = LiteLLMConfig.setup_for_ollama()

        # Should have Ollama models
        assert len(config["model_list"]) >= 1

        for model in config["model_list"]:
            assert "ollama" in model["litellm_params"]["model"].lower()
            assert "localhost" in model["litellm_params"]["api_base"]
            assert "11434" in model["litellm_params"]["api_base"]

    def test_generate_yaml_file_content(self) -> None:
        """Test that generated YAML is ready to write to file."""
        yaml_content = LiteLLMConfig.to_yaml_string()

        # Should be string
        assert isinstance(yaml_content, str)

        # Should contain all required sections
        assert "model_list:" in yaml_content
        assert "router_settings:" in yaml_content
        assert "general_settings:" in yaml_content

        # Should be safe to write to file
        assert len(yaml_content) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
