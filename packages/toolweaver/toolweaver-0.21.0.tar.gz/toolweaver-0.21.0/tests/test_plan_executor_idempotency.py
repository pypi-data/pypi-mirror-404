"""
Tests for PlanExecutor idempotency integration.

Phase 4.2: Idempotency Support

Validates that PlanExecutor uses idempotency cache to prevent duplicate
step execution when session has idempotency_key set.
"""


from typing import Any

import pytest

from orchestrator._internal.planning.execution_plan import (
    ExecutionPlan,
    PlanStep,
)
from orchestrator._internal.planning.plan_executor import (
    ExecutionMode,
    ExecutionPolicy,
    PlanExecutor,
)
from orchestrator.context import ExecutionContext


def create_simple_plan() -> ExecutionPlan:
    """Create a simple test plan with independent steps."""
    plan = ExecutionPlan(id="test-plan", description="Test plan for idempotency")

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


class TestPlanExecutorIdempotency:
    """Test idempotency support in PlanExecutor."""

    @pytest.mark.asyncio
    async def test_executor_without_idempotency_key_executes_normally(self) -> None:
        """Test executor works normally without idempotency_key."""
        plan = create_simple_plan()
        session = ExecutionContext(task_description="Test execution")
        # No idempotency_key set

        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, Any]:
            call_count[step.id] += 1
            return {"result": f"{step.id}_result", "value": 42}

        executor.register_task_handler("test-agent", mock_handler)

        result = await executor.execute()

        assert result.success
        assert result.completed_steps == 2
        assert call_count["step1"] == 1
        assert call_count["step2"] == 1

    @pytest.mark.asyncio
    async def test_executor_with_idempotency_key_caches_results(self) -> None:
        """Test executor caches step results when idempotency_key is set."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test execution",
            idempotency_key="test-idem-key-123",
        )

        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, Any]:
            call_count[step.id] += 1
            return {"result": f"{step.id}_result", "value": call_count[step.id]}

        executor.register_task_handler("test-agent", mock_handler)

        result = await executor.execute()

        assert result.success
        assert result.completed_steps == 2
        assert call_count["step1"] == 1
        assert call_count["step2"] == 1

        # Verify results are cached
        cache_key_1 = f"{session.idempotency_key}:step1"
        cache_key_2 = f"{session.idempotency_key}:step2"

        cached_1 = executor.idempotency_cache.get(cache_key_1)
        cached_2 = executor.idempotency_cache.get(cache_key_2)

        assert cached_1 is not None
        assert cached_1["result"] == "step1_result"
        assert cached_2 is not None
        assert cached_2["result"] == "step2_result"

    @pytest.mark.asyncio
    async def test_executor_returns_cached_results_on_replay(self) -> None:
        """Test executor returns cached results when same plan replayed."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test execution",
            idempotency_key="replay-test-key",
        )

        # First execution
        executor1 = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, Any]:
            call_count[step.id] += 1
            return {"result": f"{step.id}_result", "execution": call_count[step.id]}

        executor1.register_task_handler("test-agent", mock_handler)

        result1 = await executor1.execute()

        assert result1.success
        assert call_count["step1"] == 1
        assert call_count["step2"] == 1

        # Second execution with same idempotency_key (replay)
        plan2 = create_simple_plan()
        session2 = ExecutionContext(
            task_description="Test execution replay",
            idempotency_key="replay-test-key",  # Same key!
        )

        executor2 = PlanExecutor(plan2, mode=ExecutionMode.SEQUENTIAL, session=session2)
        # Share the same cache
        executor2.idempotency_cache = executor1.idempotency_cache

        executor2.register_task_handler("test-agent", mock_handler)

        result2 = await executor2.execute()

        # Should succeed without calling handler again
        assert result2.success
        assert result2.completed_steps == 2
        # Handler should not be called again (still 1 each)
        assert call_count["step1"] == 1
        assert call_count["step2"] == 1

        # Results should be from first execution
        step1_result = executor2.step_results.get("step1")
        step2_result = executor2.step_results.get("step2")

        assert step1_result is not None
        assert step1_result.result is not None
        assert step1_result.result["execution"] == 1
        assert step2_result is not None
        assert step2_result.result is not None
        assert step2_result.result["execution"] == 1

    @pytest.mark.asyncio
    async def test_executor_different_idempotency_keys_execute_independently(self) -> None:
        """Test different idempotency keys execute independently."""
        plan = create_simple_plan()

        # First execution with key1
        session1 = ExecutionContext(
            task_description="Test execution 1",
            idempotency_key="key-1",
        )

        executor1 = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session1)

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, Any]:
            call_count[step.id] += 1
            return {"result": f"{step.id}_result", "key": call_count[step.id]}

        executor1.register_task_handler("test-agent", mock_handler)

        result1 = await executor1.execute()

        assert result1.success
        assert call_count["step1"] == 1
        assert call_count["step2"] == 1

        # Second execution with key2 (different key)
        plan2 = create_simple_plan()
        session2 = ExecutionContext(
            task_description="Test execution 2",
            idempotency_key="key-2",  # Different key!
        )

        executor2 = PlanExecutor(plan2, mode=ExecutionMode.SEQUENTIAL, session=session2)
        # Share cache to verify different keys don't conflict
        executor2.idempotency_cache = executor1.idempotency_cache

        executor2.register_task_handler("test-agent", mock_handler)

        result2 = await executor2.execute()

        # Should execute normally (different key)
        assert result2.success
        assert result2.completed_steps == 2
        # Handler should be called again for new key
        assert call_count["step1"] == 2
        assert call_count["step2"] == 2

    @pytest.mark.asyncio
    async def test_executor_partial_cache_completes_remaining_steps(self) -> None:
        """Test executor with partial cache completes only uncached steps."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test execution",
            idempotency_key="partial-cache-key",
        )

        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        # Pre-populate cache with step1 result
        cache_key_1 = f"{session.idempotency_key}:step1"
        executor.idempotency_cache.store(
            cache_key_1,
            {"result": "step1_cached", "value": 99},
            status="success",
        )

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, Any]:
            call_count[step.id] += 1
            return {"result": f"{step.id}_fresh", "value": 42}

        executor.register_task_handler("test-agent", mock_handler)

        result = await executor.execute()

        assert result.success
        assert result.completed_steps == 2

        # step1 should use cached result (not called)
        assert call_count["step1"] == 0
        # step2 should execute normally (called once)
        assert call_count["step2"] == 1

        # Verify step1 used cached result
        step1_result = executor.step_results.get("step1")
        assert step1_result is not None
        assert step1_result.result is not None
        assert step1_result.result["result"] == "step1_cached"
        assert step1_result.result["value"] == 99

        # Verify step2 used fresh result
        step2_result = executor.step_results.get("step2")
        assert step2_result is not None
        assert step2_result.result is not None
        assert step2_result.result["result"] == "step2_fresh"
        assert step2_result.result["value"] == 42

    @pytest.mark.asyncio
    async def test_executor_tracks_cache_hits_in_session_metadata(self) -> None:
        """Test executor records cache hits in session metadata."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test execution",
            idempotency_key="metadata-test-key",
        )

        executor = PlanExecutor(plan, mode=ExecutionMode.SEQUENTIAL, session=session)

        # Pre-populate cache
        cache_key_1 = f"{session.idempotency_key}:step1"
        executor.idempotency_cache.store(
            cache_key_1,
            {"result": "cached"},
            status="success",
        )

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            return {"result": "fresh"}

        executor.register_task_handler("test-agent", mock_handler)

        await executor.execute()

        # Check metadata for cache hit
        metadata = session.metadata

        # step1 should have cache hit metadata
        assert "step_step1_cached" in metadata
        cached_meta = metadata["step_step1_cached"]
        assert cached_meta["cache_hit"] is True
        assert cached_meta["step_id"] == "step1"

        # step2 should have normal started/completed metadata (no cache hit)
        assert "step_step2_started" in metadata
        assert "step_step2_completed" in metadata
        assert "step_step2_cached" not in metadata

    @pytest.mark.asyncio
    async def test_executor_failed_steps_not_cached(self) -> None:
        """Test executor does not cache failed step results."""
        plan = create_simple_plan()
        session = ExecutionContext(
            task_description="Test execution",
            idempotency_key="failure-test-key",
        )

        executor = PlanExecutor(
            plan,
            mode=ExecutionMode.SEQUENTIAL,
            session=session,
            policy=ExecutionPolicy.CONTINUE,  # Continue on failure
        )

        call_count = {"step1": 0, "step2": 0}

        async def mock_handler(step: PlanStep) -> dict[str, str]:
            call_count[step.id] += 1
            if step.id == "step1":
                raise ValueError("Step 1 failed")
            return {"result": f"{step.id}_result"}

        executor.register_task_handler("test-agent", mock_handler)

        result = await executor.execute()

        # Execution should fail due to step1
        assert not result.success
        assert result.failed_steps == 1

        # Verify step1 result is NOT cached (failed)
        cache_key_1 = f"{session.idempotency_key}:step1"
        cached_1 = executor.idempotency_cache.get(cache_key_1)
        assert cached_1 is None  # Should not be cached

        # Verify metadata tracks failure
        assert "step_step1_failed" in session.metadata
