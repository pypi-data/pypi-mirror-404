"""
Tests for Workflow Suspension (Phase 8.2)
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from orchestrator._internal.workflows.engine import WorkflowExecutor
from orchestrator._internal.workflows.workflow import (
    StepStatus,
    WorkflowStep,
    WorkflowTemplate,
)


@pytest.fixture
def mock_tool_executor() -> Any:
    executor = Mock()
    executor.execute = AsyncMock(return_value={"status": "executed"})
    return executor

@pytest.mark.asyncio
async def test_execution_suspends_on_approval(mock_tool_executor: Any) -> None:
    step = WorkflowStep(step_id="step1", tool_name="tool1", parameters={}, requires_approval=True)
    template = WorkflowTemplate(name="suspend", description="desc", steps=[step])

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template)

    assert context.suspension is not None
    assert context.suspension.step_id == "step1"
    assert context.get_status("step1") == StepStatus.SUSPENDED
    assert mock_tool_executor.execute.call_count == 0

@pytest.mark.asyncio
async def test_execution_resumes_with_approval(mock_tool_executor: Any) -> None:
    step = WorkflowStep(step_id="step1", tool_name="tool1", parameters={}, requires_approval=True)
    template = WorkflowTemplate(name="suspend", description="desc", steps=[step])

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)

    # 1. Provide approval in variables
    initial_vars = {"__approvals__": ["step1"]}
    context = await engine.execute(template, initial_variables=initial_vars)

    assert context.suspension is None
    assert context.get_status("step1") == StepStatus.SUCCESS
    assert mock_tool_executor.execute.call_count == 1

@pytest.mark.asyncio
async def test_partial_execution_before_suspension(mock_tool_executor: Any) -> None:
    # Step 1 (Normal) -> Step 2 (Approval)
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
        WorkflowStep(step_id="step2", tool_name="tool2", parameters={}, depends_on=["step1"], requires_approval=True)
    ]
    template = WorkflowTemplate(name="partial", description="desc", steps=steps)
    engine = WorkflowExecutor(tool_executor=mock_tool_executor)

    context = await engine.execute(template)

    assert context.is_success("step1")
    assert context.get_status("step2") == StepStatus.SUSPENDED
    assert context.suspension is not None
    assert context.suspension.step_id == "step2"
    assert mock_tool_executor.execute.call_count == 1

@pytest.mark.asyncio
async def test_downstream_waits_for_suspension(mock_tool_executor: Any) -> None:
    # Step 1 (Approval) -> Step 2 (Depends on 1)
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={}, requires_approval=True),
        WorkflowStep(step_id="step2", tool_name="tool2", parameters={}, depends_on=["step1"])
    ]
    template = WorkflowTemplate(name="wait", description="desc", steps=steps)
    engine = WorkflowExecutor(tool_executor=mock_tool_executor)

    context = await engine.execute(template)

    assert context.get_status("step1") == StepStatus.SUSPENDED
    # Step 2 shouldn't run. Since it waits, it never enters RUNNING state, so status is None (missing).
    assert context.get_status("step2") is None

    assert mock_tool_executor.execute.call_count == 0
