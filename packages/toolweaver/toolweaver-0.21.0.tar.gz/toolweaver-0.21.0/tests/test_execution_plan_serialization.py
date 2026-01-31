from datetime import datetime

from orchestrator._internal.planning.execution_plan import (
    ExecutionPlan,
    PlanStatus,
    PlanStep,
    StepStatus,
)


def test_plan_step_to_from_dict() -> None:
    start = datetime(2026, 1, 20, 12, 0, 0)
    end = datetime(2026, 1, 20, 12, 5, 0)
    step = PlanStep(
        id="s1",
        task_description="Do work",
        agent_profile="default",
        depends_on=["s0"],
        can_be_parallel=False,
        required_capabilities=["compute"],
        status=StepStatus.COMPLETED,
        priority=2,
        estimated_duration=300.0,
        timeout=600.0,
        result={"ok": True},
        error=None,
        start_time=start,
        end_time=end,
    )

    data = step.to_dict()
    restored = PlanStep.from_dict(data)

    assert restored.id == step.id
    assert restored.task_description == step.task_description
    assert restored.agent_profile == step.agent_profile
    assert restored.depends_on == step.depends_on
    assert restored.can_be_parallel == step.can_be_parallel
    assert restored.required_capabilities == step.required_capabilities
    assert restored.status == step.status
    assert restored.priority == step.priority
    assert restored.estimated_duration == step.estimated_duration
    assert restored.timeout == step.timeout
    assert restored.result == step.result
    assert restored.error == step.error
    assert restored.start_time == step.start_time
    assert restored.end_time == step.end_time


def test_execution_plan_to_from_json_roundtrip() -> None:
    step1 = PlanStep(id="s1", task_description="First", agent_profile="default")
    step2 = PlanStep(
        id="s2",
        task_description="Second",
        agent_profile="default",
        depends_on=["s1"],
        status=StepStatus.READY,
    )

    plan = ExecutionPlan(
        id="plan-123",
        description="Test plan",
        steps=[step1, step2],
        dependencies={"s1": [], "s2": ["s1"]},
        status=PlanStatus.READY,
        created_at=datetime(2026, 1, 20, 11, 0, 0),
        started_at=datetime(2026, 1, 20, 11, 1, 0),
        completed_at=None,
    )

    json_str = plan.to_json()
    restored = ExecutionPlan.from_json(json_str)

    assert restored.id == plan.id
    assert restored.description == plan.description
    assert restored.status == plan.status
    assert restored.dependencies == plan.dependencies
    assert len(restored.steps) == 2
    assert restored.steps[0].id == "s1"
    assert restored.steps[1].depends_on == ["s1"]
    assert restored.created_at == plan.created_at
    assert restored.started_at == plan.started_at
    assert restored.completed_at == plan.completed_at


def test_execution_plan_to_dict_contains_expected_fields() -> None:
    step = PlanStep(id="s1", task_description="Only", agent_profile="default")
    plan = ExecutionPlan(id="pid", description="desc", steps=[step])

    data = plan.to_dict()

    assert data["id"] == "pid"
    assert data["description"] == "desc"
    assert isinstance(data["steps"], list)
    assert data["steps"][0]["id"] == "s1"
    assert "dependencies" in data
    assert "status" in data
    assert "created_at" in data
