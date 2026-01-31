"""
LiteLLM Configuration for ToolWeaver

This module provides LiteLLM configuration and setup for routing Claude SDK
calls through LiteLLM proxy to various model backends.

LiteLLM enables:
- Single orchestrator interface for multiple model providers
- Automatic format translation (Anthropic ↔ OpenAI ↔ other providers)
- Rate limiting, load balancing, automatic failover
- Support for local models (Ollama) and hosted services

Architecture:
    Your App
        ↓
    ClaudeOrchestrator (with base_url)
        ↓
    LiteLLM Proxy (http://localhost:4000)
        ↓
    ├─ Ollama (local models: llama3.1, qwen2.5, etc.)
    ├─ OpenAI (GPT-4, etc.)
    ├─ Claude (via Anthropic API)
    └─ Other providers

Usage:

    1. Start LiteLLM proxy with this config:
       $ litellm --config config/litellm.yaml

    2. In your code:
       from orchestrator.adapters import ClaudeOrchestrator, OrchestratorConfig

       config = OrchestratorConfig(
           model="claude-3-5-sonnet-20241022",
           base_url="http://localhost:4000/v1",  # LiteLLM proxy
           api_key="dummy"  # LiteLLM doesn't use this
       )
       orchestrator = ClaudeOrchestrator(config)

       # Now Claude SDK calls are routed through LiteLLM to Ollama/OpenAI/etc.
       result = orchestrator.plan("Your task")

See docs/integration/claude-sdk-configuration.md for more details.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LiteLLMConfig:
    """Configuration helper for LiteLLM proxy setup."""

    @staticmethod
    def get_default_config() -> dict[str, Any]:
        """
        Get default LiteLLM configuration for development.

        Returns:
            Dictionary for litellm.yaml format
        """
        return {
            "model_list": [
                {
                    "model_name": "claude-orchestrator",
                    "litellm_params": {
                        "model": "ollama/llama3.1:8b",
                        "api_base": "http://localhost:11434",
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                },
                {
                    "model_name": "claude-fast",
                    "litellm_params": {
                        "model": "ollama/qwen2.5:7b",
                        "api_base": "http://localhost:11434",
                        "temperature": 0.5,
                        "max_tokens": 2048,
                    },
                },
                {
                    "model_name": "openai-gpt4",
                    "litellm_params": {
                        "model": "gpt-4-turbo-preview",
                        "api_base": "https://api.openai.com/v1",
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                },
                {
                    "model_name": "claude-direct",
                    "litellm_params": {
                        "model": "claude-3-5-sonnet-20241022",
                        "api_base": "https://api.anthropic.com",
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                },
            ],
            "router_settings": {
                "fallbacks": [
                    {
                        "claude-orchestrator": ["claude-fast", "openai-gpt4"]
                    }
                ]
            },
            "general_settings": {
                "enable_openai_tools": True,
                "enable_request_logging": True,
            },
        }

    @staticmethod
    def to_yaml_string() -> str:
        """
        Convert config to YAML format for litellm.yaml file.

        Returns:
            YAML formatted string
        """
        config = LiteLLMConfig.get_default_config()

        yaml_lines = [
            "# LiteLLM Configuration for ToolWeaver",
            "# Generated configuration for routing Claude SDK calls through LiteLLM proxy",
            "",
            "model_list:",
        ]

        for model in config["model_list"]:
            yaml_lines.append(f'  - model_name: {model["model_name"]}')
            yaml_lines.append("    litellm_params:")
            for key, value in model["litellm_params"].items():
                if isinstance(value, str):
                    yaml_lines.append(f'      {key}: "{value}"')
                else:
                    yaml_lines.append(f"      {key}: {value}")

        yaml_lines.append("")
        yaml_lines.append("router_settings:")
        yaml_lines.append("  fallbacks:")
        for fallback in config["router_settings"]["fallbacks"]:
            for model_name, fallback_list in fallback.items():
                yaml_lines.append(f'    - {model_name}:')
                for fallback_model in fallback_list:
                    yaml_lines.append(f'        - {fallback_model}')

        yaml_lines.append("")
        yaml_lines.append("general_settings:")
        for key, value in config["general_settings"].items():
            if isinstance(value, bool):
                yaml_lines.append(f"  {key}: {str(value).lower()}")
            else:
                yaml_lines.append(f'  {key}: "{value}"')

        return "\n".join(yaml_lines)

    @staticmethod
    def setup_for_ollama() -> dict[str, Any]:
        """
        Get LiteLLM configuration for Ollama-only setup (local development).

        Returns:
            Configuration dictionary
        """
        return {
            "model_list": [
                {
                    "model_name": "claude-orchestrator",
                    "litellm_params": {
                        "model": "ollama/llama3.1:8b",
                        "api_base": "http://localhost:11434",
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                },
                {
                    "model_name": "claude-fast",
                    "litellm_params": {
                        "model": "ollama/qwen2.5:7b",
                        "api_base": "http://localhost:11434",
                        "temperature": 0.5,
                        "max_tokens": 2048,
                    },
                },
            ],
            "router_settings": {
                "fallbacks": [{"claude-orchestrator": ["claude-fast"]}]
            },
            "general_settings": {
                "enable_openai_tools": True,
                "enable_request_logging": True,
            },
        }

    @staticmethod
    def get_orchestrator_config_for_litellm(
        model_name: str = "claude-orchestrator",
        proxy_url: str = "http://localhost:4000/v1",
    ) -> dict[str, Any]:
        """
        Get OrchestratorConfig dictionary for LiteLLM proxy routing.

        Args:
            model_name: Model name to use (from litellm.yaml model_list)
            proxy_url: LiteLLM proxy URL

        Returns:
            Configuration dictionary for OrchestratorConfig
        """
        return {
            "model": model_name,
            "base_url": proxy_url,
            "api_key": "unused",  # LiteLLM doesn't validate this
            "temperature": 0.2,
            "max_tokens": 4096,
        }


def print_setup_instructions() -> None:
    """Print setup instructions for LiteLLM."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         LiteLLM Setup Instructions for ToolWeaver                 ║
╚═══════════════════════════════════════════════════════════════════╝

1. INSTALL DEPENDENCIES:
   $ pip install litellm anthropic

2. PREPARE OLLAMA (for local models):
   $ ollama serve
   (Keep running in another terminal)

3. GENERATE LITELLM CONFIG:
   $ python -c "
   from orchestrator.adapters.litellm_config import LiteLLMConfig
   with open('config/litellm.yaml', 'w') as f:
       f.write(LiteLLMConfig.to_yaml_string())
   print('✓ config/litellm.yaml created')
   "

4. START LITELLM PROXY:
   $ litellm --config config/litellm.yaml --port 4000

5. USE IN YOUR CODE:
   from orchestrator.adapters import ClaudeOrchestrator, OrchestratorConfig
   from orchestrator.adapters.litellm_config import LiteLLMConfig

   config_dict = LiteLLMConfig.get_orchestrator_config_for_litellm()
   config = OrchestratorConfig(**config_dict)
   orchestrator = ClaudeOrchestrator(config)
   result = orchestrator.plan("Your task here")

6. VERIFY:
   Try accessing http://localhost:4000/health
   Should return status information

TROUBLESHOOTING:

- "Connection refused" on port 4000:
  → Start LiteLLM proxy: litellm --config config/litellm.yaml

- "Ollama not found":
  → Start Ollama: ollama serve
  → Check http://localhost:11434 is accessible

- "Model not found in Ollama":
  → Pull model: ollama pull llama3.1:8b
  → Pull another: ollama pull qwen2.5:7b

- "KeyError: 'model_name'":
  → Check config/litellm.yaml syntax (YAML format)
  → Restart LiteLLM proxy

For more details, see: docs/integration/claude-sdk-configuration.md
    """)
