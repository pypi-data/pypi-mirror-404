"""Tests for orchestrator contract compliance.

This module tests that orchestrator implementations comply with
the OrchestratorBackend contract.

Integration tests that require real network access are gated by
the RUN_CLAUDE_INTEGRATION environment variable.
"""

import os
from typing import Any

import pytest

from orchestrator.adapters.claude_orchestrator import ClaudeOrchestrator
from orchestrator.adapters.orchestrator_interface import OrchestratorConfig
from orchestrator.adapters.production.contract import (
    OrchestratorContractTests,
    run_contract_validation,
    validate_orchestrator_compliance,
)

should_skip_integration = os.getenv("RUN_CLAUDE_INTEGRATION") != "true"


@pytest.mark.skipif(
    should_skip_integration,
    reason="Skipping Claude integration tests. Set RUN_CLAUDE_INTEGRATION=true to run.",
)
class TestClaudeOrchestratorContract(OrchestratorContractTests):
    """Contract tests for ClaudeOrchestrator implementation."""

    def create_orchestrator(self, config: OrchestratorConfig) -> ClaudeOrchestrator:
        """Create Claude orchestrator instance."""
        # Ensure API key is set for testing
        if not config.api_key:
            config.api_key = os.getenv("TEST_ANTHROPIC_API_KEY", "test-api-key")
        return ClaudeOrchestrator(config)


class TestContractValidationHelpers:
    """Test contract validation helper functions."""

    def test_validate_compliance_valid(self) -> None:
        """Test validation with compliant orchestrator."""
        pytest.importorskip("anthropic")
        # Load test configuration from environment
        # TEST_MODEL_NAME: Model for testing (default: claude-3-5-sonnet-20241022)
        # TEST_ANTHROPIC_API_KEY: API key for contract tests
        model = os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022")
        api_key = os.getenv("TEST_ANTHROPIC_API_KEY", "test-key")
        config = OrchestratorConfig(model=model, api_key=api_key)
        orch = ClaudeOrchestrator(config)

        assert validate_orchestrator_compliance(orch) is True

    def test_validate_compliance_missing_method(self) -> None:
        """Test validation with missing method."""

        class IncompleteOrchestrator:
            def __init__(self) -> None:
                self.config = OrchestratorConfig(model="test")

            async def plan(self, prompt: str) -> str:
                return "result"

        orch = IncompleteOrchestrator()
        assert validate_orchestrator_compliance(orch) is False  # type: ignore[arg-type]

    def test_validate_compliance_missing_config(self) -> None:
        """Test validation with missing config."""

        class NoConfigOrchestrator:
            async def plan(self, prompt: str) -> str:
                return "result"

            async def plan_streaming(self, prompt: str) -> Any:
                yield "chunk"

            def get_conversation_history(self) -> list[str]:
                return []

            def clear_conversation_history(self) -> None:
                pass

            def add_tool_result(self, tool_call_id: str, result: str, is_error: bool = False) -> None:
                pass

        orch = NoConfigOrchestrator()
        assert validate_orchestrator_compliance(orch) is False  # type: ignore[arg-type]

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        should_skip_integration,
        reason="Skipping Claude integration tests. Set RUN_CLAUDE_INTEGRATION=true to run.",
    )
    async def test_run_contract_validation_success(self) -> None:
        """Test programmatic contract validation with valid orchestrator."""
        # Load test configuration from environment
        model = os.getenv("TEST_MODEL_NAME", "claude-3-5-sonnet-20241022")
        api_key = os.getenv("TEST_ANTHROPIC_API_KEY", "test-key")
        config = OrchestratorConfig(model=model, api_key=api_key)
        orch = ClaudeOrchestrator(config)

        results = await run_contract_validation(orch)

        assert results["compliant"] is True
        assert len(results["errors"]) == 0

    @pytest.mark.asyncio
    async def test_run_contract_validation_failure(self) -> None:
        """Test programmatic contract validation with invalid orchestrator."""

        class BrokenOrchestrator:
            def __init__(self) -> None:
                self.config = OrchestratorConfig(model="test")

            async def plan(self, prompt: str) -> str:
                return "not a PlanResult"

            async def plan_streaming(self, prompt: str) -> Any:
                yield "chunk"

            def get_conversation_history(self) -> list[str]:
                return []

            def clear_conversation_history(self) -> None:
                pass

            def add_tool_result(self, tool_call_id: str, result: str, is_error: bool = False) -> None:
                pass

        orch = BrokenOrchestrator()
        results = await run_contract_validation(orch)  # type: ignore[arg-type]

        assert results["compliant"] is False
        assert len(results["errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
