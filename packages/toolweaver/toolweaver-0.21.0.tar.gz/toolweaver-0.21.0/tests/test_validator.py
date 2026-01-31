"""
Tests for Function Gemma Validator (Phase 7.2)
"""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from orchestrator._internal.mcp.function_gemma_validator import (
    ToolValidator,
    ValidationMode,
)


@pytest.fixture
def validator() -> Any:
    return ToolValidator(mode=ValidationMode.ADVISORY, model_name="test-model")


@patch("requests.post")
def test_validation_success(mock_post: Any, validator: Any) -> None:
    """Test successful validation passthrough."""
    # Mock Ollama response
    mock_response = {
        "valid": True,
        "reason": None,
        "corrected": {"arg": 1}
    }
    mock_post.return_value.json.return_value = {"response": json.dumps(mock_response)}
    mock_post.return_value.raise_for_status = MagicMock()

    valid, params, reason = validator.validate(
        "test_tool",
        {"arg": 1},
        {"properties": {"arg": {"type": "integer"}}}
    )

    assert valid is True
    assert params == {"arg": 1}
    assert reason is None
    mock_post.assert_called_once()


@patch("requests.post")
def test_validation_failure_strict(mock_post: Any) -> None:
    """Test strict mode blocks execution."""
    validator = ToolValidator(mode=ValidationMode.STRICT)

    mock_response = {
        "valid": False,
        "reason": "Invalid type",
        "corrected": {}
    }
    mock_post.return_value.json.return_value = {"response": json.dumps(mock_response)}

    valid, _, reason = validator.validate("t", {"a": "bad"}, {})

    assert valid is False
    assert reason == "Invalid type"


@patch("requests.post")
def test_validation_correction(mock_post: Any, validator: Any) -> None:
    """Test validator providing corrections."""
    mock_response = {
        "valid": False, # Marked invalid logic but provided correction
        "reason": "String instead of Int",
        "corrected": {"age": 25}
    }
    mock_post.return_value.json.return_value = {"response": json.dumps(mock_response)}

    # In Advisory mode, false valid + correction -> allowed
    valid, params, reason = validator.validate("t", {"age": "25"}, {})

    assert valid is True # Advisory allows it
    assert params == {"age": 25} # Uses correction
    assert reason == "String instead of Int"


def test_disabled_mode() -> None:
    """Test disabled mode skips network calls."""
    validator = ToolValidator(mode=ValidationMode.DISABLED)
    with patch("requests.post") as mock_post:
        valid, _, _ = validator.validate("t", {}, {})
        assert valid is True
        mock_post.assert_not_called()
