"""
Tests for PlanExecutor streaming execution.

Phase 4.2: Streaming Execution Support

Validates that PlanExecutor can stream execution events in real-time
for chat app integration and progress monitoring.
"""

from datetime import datetime

import pytest

from orchestrator._internal.planning.execution_plan import (
    ExecutionPlan,
    PlanStep,
)
from orchestrator._internal.planning.plan_executor import (
    ExecutionMode,
    ExecutionPolicy,
    PlanExecutor,
    StreamEvent,
    StreamEventType,
)
from orchestrator.context import ExecutionContext


def create_simple_plan() -> ExecutionPlan:
    """Create a simple test plan with independent steps."""
    plan = ExecutionPlan(id="test-plan", description="Test plan for streaming")

    step1 = PlanStep(
        id="step1",
        task_description="Task 1",
        agent_profile="test-agent",
    )
    step2 = PlanStep(
        id="step2",
        task_description="Task 2",
        agent_profile="test-agent",
    )

    plan.add_step(step1)
    plan.add_step(step2)

    return plan


class TestPlanExecutorStreaming:
    """Test streaming execution functionality."""

    @pytest.mark.asyncio
    async def test_streaming_yields_plan_started_event(self) -> None:
        """Test streaming emits plan started event."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": "ok"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # First event should be plan started
        assert len(events) > 0
        first_event = events[0]
        assert isinstance(first_event, StreamEvent)
        assert first_event.event_type == StreamEventType.PLAN_STARTED
        assert first_event.plan_id == "test-plan"
        assert first_event.data is not None
        first_event_data = first_event.data
        assert first_event_data["description"] == "Test plan for streaming"
        assert first_event_data["total_steps"] == 2

    @pytest.mark.asyncio
    async def test_streaming_yields_step_events(self) -> None:
        """Test streaming emits step started and completed events."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": f"{step.id}_result"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # Filter step events
        step_events: list[StreamEvent] = [e for e in events if e.step_id is not None]

        # Should have: step1_started, step1_completed, step2_started, step2_completed
        assert len(step_events) >= 4

        # Check step1 events
        step1_started = next(
            e
            for e in step_events
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_STARTED
        )
        assert step1_started.data is not None
        step1_started_data = step1_started.data
        assert step1_started_data["task_description"] == "Task 1"
        assert step1_started_data["agent_profile"] == "test-agent"

        step1_completed = next(
            e
            for e in step_events
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_COMPLETED
        )
        assert step1_completed.data is not None
        step1_completed_data = step1_completed.data
        assert step1_completed_data["result"]["result"] == "step1_result"
        assert "duration" in step1_completed_data

    @pytest.mark.asyncio
    async def test_streaming_yields_plan_completed_event(self) -> None:
        """Test streaming emits plan completed event at end."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": "ok"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # Last event should be plan completed
        last_event = events[-1]
        assert last_event.event_type == StreamEventType.PLAN_COMPLETED
        assert last_event.plan_id == "test-plan"
        assert last_event.data is not None
        last_event_data = last_event.data
        assert last_event_data["completed_steps"] == 2
        assert last_event_data["failed_steps"] == 0
        assert "duration" in last_event_data
        assert "success_rate" in last_event_data

    @pytest.mark.asyncio
    async def test_streaming_handles_step_failure(self) -> None:
        """Test streaming emits step failed events."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(
            plan,
            mode=ExecutionMode.SEQUENTIAL,
            session=session,
            policy=ExecutionPolicy.CONTINUE,  # Continue on failure
        )

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            if step.id == "step1":
                raise ValueError("Step 1 failed")
            return {"result": "ok"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # Find step1 failed event
        step1_failed = next(
            e
            for e in events
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_FAILED
        )
        assert step1_failed.error == "Step 1 failed"
        assert step1_failed.data is not None
        assert "duration" in step1_failed.data

        # Plan should complete (with failures)
        last_event = events[-1]
        assert last_event.event_type == StreamEventType.PLAN_FAILED
        assert last_event.data is not None
        assert last_event.data["failed_steps"] == 1

    @pytest.mark.asyncio
    async def test_streaming_event_ordering(self) -> None:
        """Test streaming events are emitted in correct order."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": "ok"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # Check expected order
        event_types: list[StreamEventType] = [e.event_type for e in events]

        assert event_types[0] == StreamEventType.PLAN_STARTED
        assert event_types[-1] == StreamEventType.PLAN_COMPLETED

        # Steps should be started before completed
        step1_start_idx = next(
            i
            for i, e in enumerate(events)
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_STARTED
        )
        step1_complete_idx = next(
            i
            for i, e in enumerate(events)
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_COMPLETED
        )
        assert step1_start_idx < step1_complete_idx

    @pytest.mark.asyncio
    async def test_streaming_event_to_dict(self) -> None:
        """Test StreamEvent to_dict for JSON serialization."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": "ok"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # Convert first event to dict
        event_dict = events[0].to_dict()

        assert "event_type" in event_dict
        assert "timestamp" in event_dict
        assert "plan_id" in event_dict
        assert event_dict["event_type"] == "plan_started"
        assert event_dict["plan_id"] == "test-plan"

        # Check timestamp is ISO format string
        assert isinstance(event_dict["timestamp"], str)
        # Should be parseable
        datetime.fromisoformat(event_dict["timestamp"])

    @pytest.mark.asyncio
    async def test_streaming_can_be_consumed_incrementally(self) -> None:
        """Test streaming allows incremental consumption."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test streaming")
        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        call_count = 0

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"result": f"result_{call_count}"}

        executor.register_task_handler("test-agent", mock_handler)

        # Consume events one at a time
        event_count = 0
        async for event in executor.execute_streaming():
            event_count += 1
            # Verify we can process events as they arrive
            assert isinstance(event, StreamEvent)

            # Check we're seeing events before all steps complete
            if event.event_type == StreamEventType.STEP_COMPLETED:
                if event.step_id == "step1":
                    # step1 completed, but step2 not started yet
                    assert call_count == 1

        # All events processed
        assert event_count > 0
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_streaming_with_idempotency_caching(self) -> None:
        """Test streaming works with idempotency caching."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test streaming",
            idempotency_key="stream-cache-test",
        )

        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        # Pre-populate cache for step1
        cache_key = f"{session.idempotency_key}:step1"
        executor.idempotency_cache.store(cache_key, {"result": "cached"}, status="success")

        call_count: dict[str, int] = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            call_count[step.id] += 1
            return {"result": "fresh"}

        executor.register_task_handler("test-agent", mock_handler)

        events: list[StreamEvent] = []
        async for event in executor.execute_streaming():
            events.append(event)

        # step1 should use cache (not called)
        assert call_count["step1"] == 0
        # step2 should execute normally
        assert call_count["step2"] == 1

        # Find step1 completed event
        step1_completed = next(
            e
            for e in events
            if e.step_id == "step1" and e.event_type == StreamEventType.STEP_COMPLETED
        )
        # Should have cached result
        assert step1_completed.data is not None
        assert step1_completed.data["result"]["result"] == "cached"
