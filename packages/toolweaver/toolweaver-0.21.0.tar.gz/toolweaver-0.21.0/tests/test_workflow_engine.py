"""
Tests for Workflow Execution Engine (Phase 8.1)
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
async def test_simple_linear_workflow(mock_tool_executor: Any) -> None:
    """Test A -> B execution"""
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={"p": 1}),
        WorkflowStep(step_id="step2", tool_name="tool2", parameters={"p": 2}, depends_on=["step1"])
    ]
    template = WorkflowTemplate(name="linear", description="desc", steps=steps)

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template)

    assert context is not None
    assert context.is_success("step1")
    assert context.is_success("step2")
    assert mock_tool_executor.execute.call_count == 2

    # Check execution order
    calls = mock_tool_executor.execute.call_args_list
    assert calls[0][0][0] == "tool1"
    assert calls[1][0][0] == "tool2"

@pytest.mark.asyncio
async def test_parallel_workflow(mock_tool_executor: Any) -> None:
    """
    Test parallel execution:
    Step 1
      |-> Step 2
      |-> Step 3
    Step 4 (depends on 2 & 3)
    """
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
        WorkflowStep(step_id="step2", tool_name="tool2", parameters={}, depends_on=["step1"]),
        WorkflowStep(step_id="step3", tool_name="tool3", parameters={}, depends_on=["step1"]),
        WorkflowStep(step_id="step4", tool_name="tool4", parameters={}, depends_on=["step2", "step3"]),
    ]
    template = WorkflowTemplate(name="parallel", description="desc", steps=steps)

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template)

    assert context is not None
    assert context.is_success("step4")
    assert mock_tool_executor.execute.call_count == 4

    # Verify levels via _resolve_dependencies manually to ensure correctness of DAG
    levels = engine._resolve_dependencies(steps)
    assert len(levels) == 3
    # Level 1: step1
    assert len(levels[0]) == 1
    assert levels[0][0].step_id == "step1"
    # Level 2: step2, step3
    assert len(levels[1]) == 2
    level2_ids = {s.step_id for s in levels[1]}
    assert level2_ids == {"step2", "step3"}
    # Level 3: step4
    assert len(levels[2]) == 1
    assert levels[2][0].step_id == "step4"

def test_circular_dependency() -> None:
    """Test circular dependency detection"""
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={}, depends_on=["step2"]),
        WorkflowStep(step_id="step2", tool_name="tool2", parameters={}, depends_on=["step1"]),
    ]
    # Validation in __post_init__ might check for existence, but not cycle
    engine = WorkflowExecutor()

    with pytest.raises(ValueError, match="Circular dependency"):
        engine._resolve_dependencies(steps)

@pytest.mark.asyncio
async def test_condition_skipping(mock_tool_executor: Any) -> None:
    """Test conditional execution"""
    steps = [
        WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
        WorkflowStep(
            step_id="step2",
            tool_name="tool2",
            parameters={},
            depends_on=["step1"],
            condition="{{var_false}}"
        ),
        WorkflowStep(
            step_id="step3",
            tool_name="tool3",
            parameters={},
            depends_on=["step1"],
            condition="{{var_true}}"
        )
    ]
    template = WorkflowTemplate(name="cond", description="desc", steps=steps)

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template, initial_variables={"var_false": False, "var_true": True})

    assert context is not None
    assert context.is_success("step1")
    assert context.get_status("step2") == StepStatus.SKIPPED
    assert context.is_success("step3")
    assert mock_tool_executor.execute.call_count == 2 # step1 and step3

@pytest.mark.asyncio
async def test_parameter_substitution(mock_tool_executor: Any) -> None:
    """Test variable substitution in parameters"""
    mock_tool_executor.execute = AsyncMock(side_effect=[
        {"output": "hello"},
        {"result": "world"}
    ])

    steps = [
        WorkflowStep(step_id="step1", tool_name="producer", parameters={}),
        WorkflowStep(
            step_id="step2",
            tool_name="consumer",
            parameters={"input": "{{step1.output}}"},
            depends_on=["step1"]
        ),
    ]
    template = WorkflowTemplate(name="subst", description="desc", steps=steps)

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template)

    assert context is not None

    # check 2nd call args
    calls = mock_tool_executor.execute.call_args_list
    assert calls[1][0][1]["input"] == "hello"

@pytest.mark.asyncio
async def test_retry_logic(mock_tool_executor: Any) -> None:
    """Test retry on failure"""
    # Fail once, then succeed
    mock_tool_executor.execute = AsyncMock(side_effect=[
        Exception("Temporary failure"),
        {"status": "recovered"}
    ])

    steps = [
        WorkflowStep(
            step_id="step1",
            tool_name="flaky",
            parameters={},
            retry_count=2
        )
    ]
    template = WorkflowTemplate(name="retry", description="desc", steps=steps)

    engine = WorkflowExecutor(tool_executor=mock_tool_executor)
    context = await engine.execute(template)

    assert context is not None
    assert context.is_success("step1")
    assert mock_tool_executor.execute.call_count == 2
