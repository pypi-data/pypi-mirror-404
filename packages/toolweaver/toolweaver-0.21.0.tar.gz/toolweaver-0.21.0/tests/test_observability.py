import json
import os
from collections.abc import Generator
from typing import Any

import pytest

import orchestrator.observability as obs_module

# Use the new import
from orchestrator.observability import get_observability


@pytest.fixture
def observability_test_context(tmp_path: Any) -> Generator[Any, None, None]:
    """
    Sets up environment variables and resets the global singleton.
    """
    # Save original env
    orig_env = os.environ.copy()

    # Save original global
    orig_global = obs_module._observability

    # Setup
    jsonl_path = tmp_path / "observability.jsonl"
    os.environ["OBSERVABILITY_ENABLED"] = "true"
    os.environ["OBSERVABILITY_JSONL_SINK"] = "true"
    os.environ["OBSERVABILITY_JSONL_PATH"] = str(jsonl_path)
    # Disable others to keep it simple
    os.environ["OBSERVABILITY_OTLP_ENABLED"] = "false"
    os.environ["WANDB_ENABLED"] = "false"

    # Reset global
    obs_module._observability = None

    yield jsonl_path

    # Teardown
    os.environ.clear()
    os.environ.update(orig_env)
    obs_module._observability = orig_global


def test_observability_jsonl_logging(observability_test_context: Any) -> None:
    """Test that Observability logs events to JSONL when enabled."""
    jsonl_path = observability_test_context

    # Get instance (should be fresh)
    obs = get_observability()
    assert obs.config.enabled is True
    assert obs.config.jsonl_sink is True

    # Log an event
    test_event = {
        "event_type": "test_event",
        "message": "Hello World",
        "value": 42
    }
    obs.log_event(test_event)

    # Log another event
    obs.log_event({"event_type": "second_event"})

    # Verify file
    assert jsonl_path.exists(), f"Expected JSONL file at {jsonl_path}"

    content = jsonl_path.read_text(encoding="utf-8").strip()
    lines = content.splitlines()
    assert len(lines) == 2

    record1 = json.loads(lines[0])
    assert record1["event_type"] == "test_event"
    assert record1["message"] == "Hello World"
    assert "timestamp" in record1

    record2 = json.loads(lines[1])
    assert record2["event_type"] == "second_event"
