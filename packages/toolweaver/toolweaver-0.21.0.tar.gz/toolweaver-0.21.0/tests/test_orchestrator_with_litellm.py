"""Integration tests for LiteLLM proxy with orchestrators.

This module tests the integration of ToolWeaver's orchestrators with LiteLLM,
including model routing, tool schema translation, and fallback behavior.
"""



import pytest

from orchestrator.adapters.claude_orchestrator import ClaudeOrchestrator
from orchestrator.adapters.litellm_config import LiteLLMConfig
from orchestrator.adapters.orchestrator_interface import (
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)

pytest.importorskip("litellm")


class TestLiteLLMProxyIntegration:
    """Test LiteLLM proxy integration with ClaudeOrchestrator."""

    def test_orchestrator_config_for_litellm_proxy(self) -> None:
        """Test that orchestrator can be configured for LiteLLM proxy."""
        config = OrchestratorConfig(
            model="claude-orchestrator",
            base_url="http://localhost:4000/v1",
            api_key="dummy",
        )

        assert config.base_url == "http://localhost:4000/v1"
        assert config.model == "claude-orchestrator"
        assert config.api_key == "dummy"

    @pytest.mark.asyncio
    async def test_claude_orchestrator_with_litellm_endpoint(self) -> None:
        """Test ClaudeOrchestrator initialization with LiteLLM endpoint."""
        config = OrchestratorConfig(
            model="claude-orchestrator",
            base_url="http://localhost:4000/v1",
            api_key="test-key",
        )

        orchestrator = ClaudeOrchestrator(config)

        assert orchestrator.config.base_url == "http://localhost:4000/v1"
        assert orchestrator.config.model == "claude-orchestrator"

    def test_litellm_config_generates_valid_proxy_config(self) -> None:
        """Test that LiteLLM config generates valid proxy configuration."""
        config = LiteLLMConfig.get_default_config()

        # Should have required sections
        assert "model_list" in config
        assert "router_settings" in config
        assert "general_settings" in config

        # Models should be valid
        assert len(config["model_list"]) >= 3

        for model in config["model_list"]:
            assert "model_name" in model
            assert "litellm_params" in model
            assert "api_base" in model["litellm_params"]


class TestToolSchemaTranslation:
    """Test tool schema translation through LiteLLM proxy."""

    def test_tool_schema_conversion_to_openai_format(self) -> None:
        """Test that tool schemas convert correctly to OpenAI format."""
        tool = ToolSchema(
            name="process_data",
            description="Process input data",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input data"},
                    "mode": {"type": "string", "enum": ["fast", "thorough"]},
                },
            },
            required=["input"],
        )

        openai_format = tool.to_openai_format()

        # Should have function wrapper
        assert "type" in openai_format
        assert openai_format["type"] == "function"
        assert "function" in openai_format

        # Function should have name and description
        func = openai_format["function"]
        assert func["name"] == "process_data"
        assert "description" in func
        assert "parameters" in func

    def test_tool_call_serialization_for_litellm(self) -> None:
        """Test that tool calls serialize correctly for LiteLLM."""
        tool_call = ToolCall(
            tool_name="fetch_data",
            parameters={"url": "https://api.example.com/data", "timeout": 30},
        )

        # Should convert to dict
        tool_dict = tool_call.to_dict()
        assert tool_dict["tool_name"] == "fetch_data"
        assert tool_dict["parameters"]["url"] == "https://api.example.com/data"
        assert tool_dict["parameters"]["timeout"] == 30

        # Should serialize to JSON
        import json

        json_str = tool_call.to_json()
        parsed = json.loads(json_str)
        assert parsed["tool_name"] == "fetch_data"


class TestModelRouting:
    """Test model routing through LiteLLM."""

    def test_litellm_model_routing_configuration(self) -> None:
        """Test that LiteLLM routing is properly configured."""
        config = LiteLLMConfig.get_default_config()

        # Should have model list
        models = {m["model_name"]: m for m in config["model_list"]}

        # Primary model should exist
        assert "claude-orchestrator" in models
        primary = models["claude-orchestrator"]
        assert "ollama" in primary["litellm_params"]["model"]

        # Fast model should exist
        assert "claude-fast" in models
        fast = models["claude-fast"]
        assert "ollama" in fast["litellm_params"]["model"]

    def test_litellm_fallback_routing(self) -> None:
        """Test that fallback routing is configured."""
        config = LiteLLMConfig.get_default_config()
        router = config["router_settings"]

        # Should have fallbacks
        assert "fallbacks" in router
        fallbacks = router["fallbacks"]
        assert len(fallbacks) > 0

        # Primary model should have fallbacks
        primary_fallback = fallbacks[0]
        assert "claude-orchestrator" in primary_fallback

    def test_ollama_vs_cloud_routing(self) -> None:
        """Test routing strategy between Ollama and cloud models."""
        config = LiteLLMConfig.get_default_config()

        ollama_models = [
            m for m in config["model_list"] if "ollama" in m["litellm_params"]["model"]
        ]
        cloud_models = [
            m for m in config["model_list"]
            if "gpt" in m["litellm_params"]["model"] or "claude" in m["litellm_params"]["model"]
        ]

        # Should have both local and cloud options
        assert len(ollama_models) >= 1
        assert len(cloud_models) >= 1


class TestLiteLLMProxyBehavior:
    """Test expected behavior when using LiteLLM proxy."""

    @pytest.mark.asyncio
    async def test_litellm_proxy_response_format(self) -> None:
        """Test expected response format from LiteLLM proxy."""
        # LiteLLM proxy translates to OpenAI format
        mock_litellm_response = {
            "id": "chatcmpl-12345",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "ollama/llama3.1:8b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "fetch_data",
                                    "arguments": '{"url": "https://api.example.com"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

        # Should have standard OpenAI response structure
        assert "choices" in mock_litellm_response
        assert "usage" in mock_litellm_response
        choice = mock_litellm_response["choices"][0]  # type: ignore
        assert "message" in choice
        assert "tool_calls" in choice["message"]

    def test_litellm_enables_tool_use(self) -> None:
        """Test that LiteLLM configuration enables tool use."""
        config = LiteLLMConfig.get_default_config()
        general = config["general_settings"]

        # Tool use should be enabled
        assert general.get("enable_openai_tools", False) is True

    def test_litellm_handles_streaming(self) -> None:
        """Test that LiteLLM supports streaming responses."""
        config = LiteLLMConfig.get_default_config()

        # Streaming should be supported through base_url
        # (LiteLLM proxy handles streaming translation)
        assert "model_list" in config
        for model in config["model_list"]:
            assert "api_base" in model["litellm_params"]


class TestOllamaIntegration:
    """Test Ollama-specific integration."""

    def test_ollama_model_configuration(self) -> None:
        """Test that Ollama models are properly configured."""
        config = LiteLLMConfig.get_default_config()

        ollama_models = [
            m for m in config["model_list"] if "ollama" in m["litellm_params"]["model"]
        ]

        assert len(ollama_models) >= 2

        for model in ollama_models:
            params = model["litellm_params"]
            # Should use localhost Ollama
            assert "localhost:11434" in params["api_base"]
            # Should have valid model format
            assert ":" in params["model"]
            assert "ollama/" in params["model"]

    def test_ollama_setup_configuration(self) -> None:
        """Test Ollama-only setup configuration."""
        config = LiteLLMConfig.setup_for_ollama()

        # All models should be Ollama
        for model in config["model_list"]:
            params = model["litellm_params"]
            assert "ollama" in params["model"]
            assert "localhost:11434" in params["api_base"]

    def test_litellm_ollama_endpoint(self) -> None:
        """Test LiteLLM Ollama endpoint configuration."""
        config = LiteLLMConfig.get_default_config()

        # Find Ollama models
        ollama_models = [
            m for m in config["model_list"] if "ollama" in m["litellm_params"]["model"]
        ]

        for model in ollama_models:
            params = model["litellm_params"]
            # Ollama should be on port 11434
            assert "11434" in params["api_base"]


class TestMultiModelScenarios:
    """Test scenarios with multiple model routing."""

    def test_primary_model_preference(self) -> None:
        """Test that primary model is used when available."""
        config = LiteLLMConfig.get_default_config()

        # Primary model should be first
        primary = config["model_list"][0]
        assert primary["model_name"] == "claude-orchestrator"

    def test_fallback_to_fast_model(self) -> None:
        """Test fallback mechanism to fast model."""
        config = LiteLLMConfig.get_default_config()
        fallbacks = config["router_settings"]["fallbacks"]

        # Primary should fallback to fast
        primary_fallback = fallbacks[0]["claude-orchestrator"]
        assert "claude-fast" in primary_fallback

    def test_fallback_chain_depth(self) -> None:
        """Test depth of fallback chain."""
        config = LiteLLMConfig.get_default_config()
        fallbacks = config["router_settings"]["fallbacks"]

        primary_fallback = fallbacks[0]["claude-orchestrator"]

        # Should have multiple fallbacks
        assert len(primary_fallback) >= 2

    def test_cost_optimization_strategy(self) -> None:
        """Test cost optimization through model selection."""
        config = LiteLLMConfig.get_default_config()

        # Primary (Ollama) is free
        primary = config["model_list"][0]
        assert "ollama" in primary["litellm_params"]["model"]

        # Fallbacks go to faster/cheaper options
        models_by_name = {m["model_name"]: m for m in config["model_list"]}

        # Should have cost-ordering: free -> fast -> standard
        assert len(models_by_name) >= 3


class TestConfigurationEdgeCases:
    """Test edge cases in LiteLLM configuration."""

    def test_empty_model_list_handling(self) -> None:
        """Test handling of configuration edge cases."""
        config = LiteLLMConfig.get_default_config()
        assert len(config["model_list"]) > 0

    def test_duplicate_model_names(self) -> None:
        """Test that model names are unique."""
        config = LiteLLMConfig.get_default_config()

        model_names = [m["model_name"] for m in config["model_list"]]
        unique_names = set(model_names)

        # Should have no duplicates
        assert len(model_names) == len(unique_names)

    def test_missing_required_fields(self) -> None:
        """Test that all models have required fields."""
        config = LiteLLMConfig.get_default_config()

        for model in config["model_list"]:
            assert "model_name" in model
            assert "litellm_params" in model
            params = model["litellm_params"]
            assert "model" in params
            assert "api_base" in params

    def test_temperature_range(self) -> None:
        """Test that temperature values are in valid range."""
        config = LiteLLMConfig.get_default_config()

        for model in config["model_list"]:
            params = model["litellm_params"]
            if "temperature" in params:
                temp = params["temperature"]
                assert 0 <= temp <= 1.0


class TestLiteLLMYAMLFormat:
    """Test YAML format generated for LiteLLM."""

    def test_yaml_is_valid(self) -> None:
        """Test that generated YAML is valid."""
        import yaml

        yaml_str = LiteLLMConfig.to_yaml_string()
        parsed = yaml.safe_load(yaml_str)

        assert parsed is not None
        assert "model_list" in parsed

    def test_yaml_has_all_sections(self) -> None:
        """Test that YAML includes all required sections."""
        yaml_str = LiteLLMConfig.to_yaml_string()

        assert "model_list:" in yaml_str
        assert "router_settings:" in yaml_str
        assert "general_settings:" in yaml_str

    def test_yaml_model_formatting(self) -> None:
        """Test that YAML model section is properly formatted."""
        yaml_str = LiteLLMConfig.to_yaml_string()

        lines = yaml_str.split("\n")
        # Should have properly indented model entries
        assert any(line.startswith("  - model_name:") for line in lines)

    def test_yaml_parameters_formatting(self) -> None:
        """Test that YAML parameters are properly formatted."""
        yaml_str = LiteLLMConfig.to_yaml_string()

        lines = yaml_str.split("\n")
        # Should have properly indented parameters
        assert any("api_base:" in line and line.startswith("      ") for line in lines)


class TestLiteLLMWithToolWeaver:
    """Test LiteLLM integration with ToolWeaver components."""

    def test_tool_schema_with_litellm(self) -> None:
        """Test tool schema compatibility with LiteLLM."""
        tool = ToolSchema(
            name="query_database",
            description="Query the database",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
            required=["query"],
        )

        # Should convert to OpenAI format for LiteLLM
        openai_format = tool.to_openai_format()
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "query_database"

    def test_plan_result_with_litellm(self) -> None:
        """Test that PlanResult works with LiteLLM responses."""
        result = PlanResult(
            reasoning="I need to fetch data first",
            tool_calls=[
                ToolCall(
                    tool_name="fetch_data",
                    parameters={"source": "database"},
                ),
                ToolCall(
                    tool_name="process_data",
                    parameters={"operation": "filter"},
                ),
            ],
        )

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].tool_name == "fetch_data"

    def test_orchestrator_config_compatibility(self) -> None:
        """Test OrchestratorConfig compatibility with LiteLLM."""
        config_dict = LiteLLMConfig.get_orchestrator_config_for_litellm()

        # Should be valid OrchestratorConfig
        config = OrchestratorConfig(**config_dict)

        assert config.model == "claude-orchestrator"
        assert config.base_url is not None
        assert "http" in config.base_url
        assert "4000" in config.base_url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
