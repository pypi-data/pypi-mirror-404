"""
Tests for Workflow Execution with Persistence (Phase 8.3 integration)
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from orchestrator._internal.workflows.engine import WorkflowExecutor
from orchestrator._internal.workflows.persistence import FileWorkflowStore
from orchestrator._internal.workflows.workflow import StepStatus, WorkflowStep, WorkflowTemplate


@pytest.fixture
def store_dir() -> Any:
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)

@pytest.fixture
def mock_tool_executor() -> Any:
    executor = Mock()
    executor.execute = AsyncMock(side_effect=lambda name, params: {"status": "ok", "tool": name})
    return executor

@pytest.mark.asyncio
async def test_execution_saves_state(store_dir: Path, mock_tool_executor: Any) -> None:
    store = FileWorkflowStore(store_dir)
    engine = WorkflowExecutor(mock_tool_executor, store)

    step = WorkflowStep("s1", "t1", {})
    wf = WorkflowTemplate("persist", "desc", [step])
    wf_id = "test-run-1"

    await engine.execute(wf, workflow_id=wf_id)

    # Check file
    assert (store_dir / "test-run-1.json").exists()
    saved = store.load_state(wf_id)
    assert saved is not None
    assert saved.is_success("s1")

@pytest.mark.asyncio
async def test_suspend_and_resume(store_dir: Path, mock_tool_executor: Any) -> None:
    store = FileWorkflowStore(store_dir)
    engine = WorkflowExecutor(mock_tool_executor, store)

    steps = [
        WorkflowStep("s1", "t1", {}),
        WorkflowStep("s2", "t2", {}, depends_on=["s1"], requires_approval=True),
        WorkflowStep("s3", "t3", {}, depends_on=["s2"])
    ]
    wf = WorkflowTemplate("suspend-resume", "desc", steps)
    wf_id = "run-suspend"

    # Run 1: Should suspend at s2
    ctx1 = await engine.execute(wf, workflow_id=wf_id)

    assert ctx1 is not None
    assert ctx1.is_success("s1")
    assert ctx1.get_status("s2") == StepStatus.SUSPENDED
    assert ctx1.suspension is not None
    # Wait for completion of save
    state_on_disk = store.load_state(wf_id)
    assert state_on_disk is not None
    assert state_on_disk.get_status("s2") == StepStatus.SUSPENDED

    # Tool 1 called, Tool 2 not called yet
    assert mock_tool_executor.execute.call_count == 1
    assert mock_tool_executor.execute.call_args[0][0] == "t1"
    mock_tool_executor.execute.reset_mock()

    # Run 2: Resume with approval
    # We pass approval in variables
    approvals = {"__approvals__": ["s2"]}

    ctx2 = await engine.resume(wf, wf_id, additional_variables=approvals)

    assert ctx2 is not None
    assert ctx2.is_success("s1")  # Should rely on persisted state, not re-run
    assert ctx2.is_success("s2")
    assert ctx2.is_success("s3")

    # Tool 2 and 3 called. Tool 1 should NOT be called again.
    assert mock_tool_executor.execute.call_count == 2
    calls = [c[0][0] for c in mock_tool_executor.execute.call_args_list]
    assert "t2" in calls
    assert "t3" in calls
    assert "t1" not in calls

@pytest.mark.asyncio
async def test_resume_not_found(store_dir: Path) -> None:
    store = FileWorkflowStore(store_dir)
    engine = WorkflowExecutor(None, store)
    wf = WorkflowTemplate("dummy", "desc", [WorkflowStep("s1", "t1", {})])

    with pytest.raises(ValueError, match="No state found"):
        await engine.resume(wf, "non-existent")
