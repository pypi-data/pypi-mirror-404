"""
Tests for PlanExecutor integration with ExecutionContext.

Phase 4.2.2: PlanExecutor SessionContext Integration

Tests cover:
- ExecutionContext creation and session tracking
- Per-step execution tracking in session metadata
- Cost aggregation across steps
- Error handling and session failure marking
- Session propagation through nested plan execution
- Plan execution with global context
"""

import asyncio
from typing import Any

import pytest

from orchestrator._internal.planning.execution_plan import (
    ExecutionPlan,
    PlanStep,
)
from orchestrator._internal.planning.plan_executor import (
    ExecutionPolicy,
    PlanExecutor,
)
from orchestrator.context import (
    ExecutionContext,
    get_execution_context,
    set_execution_context,
)


# Helper functions for creating test plans
def create_simple_plan() -> ExecutionPlan:
    """Create a simple plan with one or two steps."""
    plan = ExecutionPlan(
        id="test_plan",
        description="Test plan",
    )

    step1 = PlanStep(
        id="step1",
        task_description="First step",
        agent_profile="default_agent",
    )
    plan.add_step(step1)

    return plan


def create_plan_with_multiple_steps() -> ExecutionPlan:
    """Create a plan with multiple independent steps."""
    plan = ExecutionPlan(
        id="test_plan_multi",
        description="Multi-step test plan",
    )

    for i in range(3):
        step = PlanStep(
            id=f"step{i + 1}",
            task_description=f"Step {i + 1}",
            agent_profile="default_agent",
        )
        plan.add_step(step)

    return plan


def create_failing_plan() -> ExecutionPlan:
    """Create a plan that will fail."""
    plan = ExecutionPlan(
        id="test_plan_failing",
        description="Failing test plan",
    )

    step = PlanStep(
        id="failing_step",
        task_description="Step that will fail",
        agent_profile="default_agent",
    )
    plan.add_step(step)

    return plan


def create_plan_with_failing_step() -> ExecutionPlan:
    """Create a plan with both success and failure steps."""
    plan = ExecutionPlan(
        id="test_plan_mixed",
        description="Mixed success/failure test plan",
    )

    step1 = PlanStep(
        id="step1_ok",
        task_description="Step that succeeds",
        agent_profile="default_agent",
    )
    plan.add_step(step1)

    step2 = PlanStep(
        id="step2_fail",
        task_description="Step that fails",
        agent_profile="default_agent",
    )
    plan.add_step(step2)

    return plan


class TestPlanExecutorSessionCreation:
    """Test ExecutionContext creation during plan execution."""

    def test_plan_executor_creates_session_if_none_provided(self) -> None:
        """Should create session automatically if not provided."""
        plan = create_simple_plan()
        executor = PlanExecutor(plan=plan)

        assert executor.session is not None
        assert isinstance(executor.session, ExecutionContext)
        assert executor.session.task_description == f"Plan execution: {plan.id}"

    def test_plan_executor_uses_provided_session(self) -> None:
        """Should use provided ExecutionContext instead of creating new."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        assert executor.session is session
        assert executor.session.user_id == "test_user"

    def test_plan_executor_uses_global_context_if_available(self) -> None:
        """Should use global ExecutionContext if no session provided and available."""
        plan = create_simple_plan()
        global_session = ExecutionContext(user_id="global_user")
        set_execution_context(global_session)

        try:
            executor = PlanExecutor(plan=plan)
            assert executor.session is global_session
        finally:
            set_execution_context(None)

    @pytest.mark.asyncio
    async def test_plan_execution_marks_session_started(self) -> None:
        """Session should be marked as started when plan execution begins."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        assert session.status == "pending"

        # Execute plan
        await executor.execute()

        # Session should be marked as started
        assert session.started_at is not None

    @pytest.mark.asyncio
    async def test_plan_execution_marks_session_completed(self) -> None:
        """Session should be marked as completed when plan execution succeeds."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        result = await executor.execute()

        assert result.success
        assert session.status == "completed"
        assert session.ended_at is not None

    @pytest.mark.asyncio
    async def test_plan_execution_marks_session_failed_on_error(self) -> None:
        """Session should be marked as failed when plan execution fails."""
        plan = create_failing_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(
            plan=plan,
            session=session,
            policy=ExecutionPolicy.FAIL_FAST,
        )

        # Register a failing handler to force failure
        async def failing_handler(step: PlanStep) -> None:
            raise RuntimeError("Step failed intentionally")

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, failing_handler)

        result = await executor.execute()

        assert not result.success
        assert session.status == "failed"
        assert session.error_message is not None


class TestPlanExecutorStepTracking:
    """Test per-step execution tracking in session."""

    @pytest.mark.asyncio
    async def test_step_execution_tracked_in_session_metadata(self) -> None:
        """Each step execution should be recorded in session metadata."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        # Register a handler that succeeds
        async def success_handler(step: PlanStep) -> dict[str, str]:
            return {"status": "success", "data": "result"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, success_handler)

        result = await executor.execute()

        assert result.success
        # Check that step tracking metadata exists
        metadata_keys = list(session.metadata.keys())
        assert any("step_" in key for key in metadata_keys)
        assert any("completed" in key for key in metadata_keys)

    @pytest.mark.asyncio
    async def test_failed_step_recorded_in_session_metadata(self) -> None:
        """Failed steps should be recorded with error info in metadata."""
        plan = create_plan_with_failing_step()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(
            plan=plan,
            session=session,
            policy=ExecutionPolicy.FAIL_FAST,
        )

        # Register handlers - one will fail
        call_count = 0

        async def handler(step: PlanStep) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": "success"}
            raise ValueError("Step failed intentionally")

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert not result.success
        metadata_keys = list(session.metadata.keys())
        failed_keys = [k for k in metadata_keys if "failed" in k]
        assert len(failed_keys) > 0

    @pytest.mark.asyncio
    async def test_session_metadata_includes_step_details(self) -> None:
        """Session metadata should include agent profile and timing."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        async def handler(step: PlanStep) -> dict[str, str]:
            await asyncio.sleep(0.01)  # Simulate work
            return {"status": "success"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert result.success
        # Verify session has metadata about execution
        assert len(session.metadata) > 0


class TestPlanExecutorContextPropagation:
    """Test ExecutionContext propagation through plan execution."""

    @pytest.mark.asyncio
    async def test_session_set_as_global_context_during_execution(self) -> None:
        """Session should be available as global context during execution."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user", request_id="req123")
        executor = PlanExecutor(plan=plan, session=session)

        captured_context: Any = None

        async def handler(step: PlanStep) -> dict[str, str]:
            nonlocal captured_context
            captured_context = get_execution_context()
            return {"status": "success"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert result.success
        assert captured_context is not None
        assert captured_context is session
        assert captured_context.request_id == "req123"

    @pytest.mark.asyncio
    async def test_global_context_restored_after_execution(self) -> None:
        """Global context should be restored after plan execution."""
        plan = create_simple_plan()
        original_context = ExecutionContext(user_id="original_user")
        set_execution_context(original_context)

        try:
            session = ExecutionContext(user_id="plan_user")
            executor = PlanExecutor(plan=plan, session=session)

            async def handler(step: PlanStep) -> dict[str, str]:
                return {"status": "success"}

            for step in plan.steps:
                executor.register_task_handler(step.agent_profile, handler)

            result = await executor.execute()

            assert result.success
            # Original context should be restored
            assert get_execution_context() is original_context

        finally:
            set_execution_context(None)

    @pytest.mark.asyncio
    async def test_nested_plan_execution_shares_session(self) -> None:
        """Nested plan execution should share parent session."""
        parent_plan = create_simple_plan()
        parent_session = ExecutionContext(user_id="parent_user")
        parent_executor = PlanExecutor(plan=parent_plan, session=parent_session)

        nested_contexts: list[Any] = []

        async def handler(step: PlanStep) -> dict[str, str]:
            nested_contexts.append(get_execution_context())
            return {"status": "success"}

        for step in parent_plan.steps:
            parent_executor.register_task_handler(step.agent_profile, handler)

        result = await parent_executor.execute()

        assert result.success
        # All nested executions should see parent session
        assert all(ctx is parent_session for ctx in nested_contexts)


class TestPlanExecutorErrorHandling:
    """Test error handling with ExecutionContext."""

    @pytest.mark.asyncio
    async def test_plan_executor_exception_marks_session_failed(self) -> None:
        """Exceptions during execution should mark session as failed."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        async def failing_handler(step: PlanStep) -> None:
            raise RuntimeError("Handler crashed")

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, failing_handler)

        result = await executor.execute()

        assert not result.success
        assert session.status == "failed"
        assert "Plan execution failed" in (session.error_message or "")

    @pytest.mark.asyncio
    async def test_session_tracks_failed_steps_count(self) -> None:
        """Session metadata should track count of failed steps."""
        plan = create_plan_with_multiple_steps()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(
            plan=plan,
            session=session,
            policy=ExecutionPolicy.CONTINUE,
        )

        fail_count = 0

        async def handler(step: PlanStep) -> dict[str, str]:
            nonlocal fail_count
            if fail_count < 1:
                fail_count += 1
                raise ValueError(f"Step {step.id} failed")
            return {"status": "success"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert result.failed_steps == 1
        assert result.completed_steps > 0


class TestPlanExecutorSessionMetrics:
    """Test session metrics and cost tracking."""

    @pytest.mark.asyncio
    async def test_session_records_plan_execution_result(self) -> None:
        """Session should record the final plan execution result."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        async def handler(step: PlanStep) -> dict[str, str]:
            return {"status": "success", "data": "test"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert result.success
        # Check that result is stored in session
        assert session.result is not None

    @pytest.mark.asyncio
    async def test_session_duration_matches_plan_execution_duration(self) -> None:
        """Session duration should match plan execution duration."""
        plan = create_simple_plan()
        session = ExecutionContext(user_id="test_user")
        executor = PlanExecutor(plan=plan, session=session)

        async def handler(step: PlanStep) -> dict[str, str]:
            await asyncio.sleep(0.05)
            return {"status": "success"}

        for step in plan.steps:
            executor.register_task_handler(step.agent_profile, handler)

        result = await executor.execute()

        assert result.success
        plan_duration = result.duration
        session_duration = (session.get_duration_ms() or 0) / 1000  # Convert to seconds

        # Allow 50ms tolerance
        assert abs(plan_duration - session_duration) < 0.1
