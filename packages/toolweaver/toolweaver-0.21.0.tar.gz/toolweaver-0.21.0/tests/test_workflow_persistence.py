"""
Tests for Workflow Persistence (Phase 8.3)
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from orchestrator._internal.workflows.persistence import FileWorkflowStore
from orchestrator._internal.workflows.workflow import ActionRequirement, StepStatus, WorkflowContext


@pytest.fixture
def temp_store_dir() -> Any:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_context_serialization() -> None:
    # Setup complex context
    ctx = WorkflowContext(initial_variables={"user": "alice"})
    ctx.set_result("step1", {"data": 123}, StepStatus.SUCCESS)
    ctx.set_result("step2", None, StepStatus.SKIPPED)
    ctx.set_error("step3", ValueError("oops"))

    req = ActionRequirement("approval", "Please approve", "step4")
    ctx.set_suspended(req)

    # Serialize
    data = ctx.to_dict()

    # Check structure
    assert data["variables"]["user"] == "alice"
    assert data["step_results"]["step1"] == {"data": 123}
    assert data["step_status"]["step1"] == "success"
    assert data["step_status"]["step2"] == "skipped"
    assert data["errors"]["step3"] == "oops"
    assert data["suspension"]["step_id"] == "step4"
    assert data["suspension"]["action_type"] == "approval"

def test_context_deserialization() -> None:
    data = {
        "variables": {"env": "prod"},
        "step_results": {"s1": "ok"},
        "step_status": {"s1": "success", "s2": "failed"},
        "errors": {"s2": "Timeout"},
        "suspension": {
            "action_type": "input",
            "description": "Provide API key",
            "step_id": "s3",
            "schema": {"type": "string"}
        }
    }

    ctx = WorkflowContext.from_dict(data)

    assert ctx.variables["env"] == "prod"
    assert ctx.get_result("s1") == "ok"
    assert ctx.is_success("s1")
    assert ctx.get_status("s2") == StepStatus.FAILED
    assert str(ctx.errors["s2"]) == "Timeout"

    assert ctx.suspension is not None
    assert ctx.suspension.step_id == "s3"
    assert ctx.suspension.action_type == "input"
    assert ctx.suspension.schema == {"type": "string"}

def test_file_store(temp_store_dir: Any) -> None:
    store = FileWorkflowStore(temp_store_dir)
    wf_id = "wf-123"

    # Create and save
    ctx = WorkflowContext({"key": "val"})
    ctx.set_result("step1", "done")
    store.save_state(wf_id, ctx)

    # Verify file exists
    path = temp_store_dir / "wf-123.json"
    assert path.exists()

    # Load and verify
    loaded_ctx = store.load_state(wf_id)
    assert loaded_ctx is not None
    assert loaded_ctx.variables["key"] == "val"
    assert loaded_ctx.get_result("step1") == "done"

    # Delete
    store.delete_state(wf_id)
    assert not path.exists()
    assert store.load_state(wf_id) is None

def test_store_invalid_load(temp_store_dir: Any) -> None:
    store = FileWorkflowStore(temp_store_dir)

    # Create corrupted file
    path = temp_store_dir / "corrupt.json"
    path.write_text("{invalid json")

    # Should handle error gracefully
    ctx = store.load_state("corrupt")
    assert ctx is None
