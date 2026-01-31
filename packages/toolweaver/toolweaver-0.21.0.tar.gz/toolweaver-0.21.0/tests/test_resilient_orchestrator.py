"""
Tests for Resilient Orchestrator (Phase 7.1)
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolSchema,
)
from orchestrator.adapters.resilient_orchestrator import ResilientOrchestrator


@pytest.fixture
def mock_backend() -> Any:
    backend = MagicMock(spec=OrchestratorBackend)
    backend.config = OrchestratorConfig()
    return backend


def test_primary_success(mock_backend: Any) -> None:
    """Test primary backend success."""
    primary = mock_backend
    backup = MagicMock(spec=OrchestratorBackend)

    orch = ResilientOrchestrator(primary, backup)

    expected_result = PlanResult(reasoning="ok", tool_calls=[])
    primary.plan.return_value = expected_result

    result = orch.plan("Hello")

    assert result == expected_result
    primary.plan.assert_called_once()
    backup.plan.assert_not_called()


def test_fallback_success(mock_backend: Any) -> None:
    """Test fallback when primary fails."""
    primary = mock_backend
    backup = MagicMock(spec=OrchestratorBackend)
    # Configure backup config attribute
    backup.config = OrchestratorConfig()

    orch = ResilientOrchestrator(primary, backup)

    # Primary raises exception
    primary.plan.side_effect = RuntimeError("Network error")

    # Backup succeeds
    expected_result = PlanResult(reasoning="backup ok", tool_calls=[])
    backup.plan.return_value = expected_result

    # primary.get_conversation_history needs to return something for sync
    primary.get_conversation_history.return_value = [{"role": "user", "content": "prev"}]

    result = orch.plan("Hello")

    assert result == expected_result
    primary.plan.assert_called_once()
    backup.plan.assert_called_once()

    # Verify history is passed to backup
    args, _ = backup.plan.call_args
    assert args[1] == [{"role": "user", "content": "prev"}]


def test_register_tools_broadcasts(mock_backend: Any) -> None:
    """Test tool registration is sent to both."""
    primary = mock_backend
    backup = MagicMock(spec=OrchestratorBackend)
    backup.config = MagicMock()

    orch = ResilientOrchestrator(primary, backup)

    tools = [ToolSchema(name="t1", description="d1", parameters={})]
    orch.register_tools(tools)

    primary.register_tools.assert_called_with(tools)
    backup.register_tools.assert_called_with(tools)
