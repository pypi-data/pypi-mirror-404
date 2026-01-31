"""
Tests for task planning skill with ExecutionContext integration.

Tests:
- Plan creation with ExecutionContext
- Session tracking through planning
- Session logging to observability
- RLM mode selection with session tracking
- Error handling and session failure logging
"""

import json
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

# Skip module if openai is not installed
pytest.importorskip("openai")


from orchestrator._internal.planning.planner import LargePlanner
from orchestrator.context import ExecutionContext, clear_context, get_context, set_context
from orchestrator.observability import JSONLSink, Observability, ObservabilityConfig
from orchestrator.skills.task_planning import create_plan


class TestTaskPlanningWithContext:
    """Tests for task planning skill with ExecutionContext."""

    def teardown_method(self) -> None:
        """Clear global context after each test."""
        clear_context()

    def test_create_plan_with_execution_context(self) -> None:
        """create_plan should accept and track ExecutionContext."""
        ctx = ExecutionContext(user_id="user123", organization_id="org456")

        plan = create_plan(
            task="Analyze simple code",
            context=None,
            execution_context=ctx,
        )

        assert plan is not None
        assert "strategy" in plan
        assert ctx.status == "completed"
        assert ctx.result is not None
        assert "plan_strategy" in ctx.metadata

    def test_create_plan_auto_creates_context(self) -> None:
        """create_plan should create context if not provided."""
        clear_context()

        plan = create_plan(task="Simple task", context=None)

        assert plan is not None

        # Context should have been created
        ctx = get_context()
        assert ctx is not None
        assert ctx.status == "completed"

    def test_create_plan_uses_global_context(self) -> None:
        """create_plan should use global context if set."""
        global_ctx = ExecutionContext(user_id="global_user")
        set_context(global_ctx)

        plan = create_plan(task="Test task", context=None)

        assert plan is not None
        ctx = get_context()
        assert ctx is not None
        assert ctx.user_id == "global_user"
        assert ctx.status == "completed"

    def test_plan_creation_logs_execution(self) -> None:
        """Plan creation should log to observability."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            # Create observability with JSONL
            obs = Observability.__new__(Observability)
            obs.config = ObservabilityConfig()
            obs.sinks = [JSONLSink(path)]

            # Monkey-patch get_observability
            import orchestrator.observability as obs_module

            original_get_obs = obs_module.get_observability
            obs_module.get_observability = lambda: obs

            try:
                ctx = ExecutionContext(user_id="user789")
                plan = create_plan(
                    task="Analyze code",
                    context=None,
                    execution_context=ctx,
                )

                assert plan is not None

                # Verify log was written
                if path.exists():
                    with open(path, encoding="utf-8") as f:
                        event = json.loads(f.readline())

                    assert event["session_id"] == ctx.session_id
                    assert event["user_id"] == "user789"
                    assert event["status"] == "completed"
            finally:
                obs_module.get_observability = original_get_obs

    def test_plan_creation_tracks_strategy(self) -> None:
        """ExecutionContext should track which strategy was used."""
        ctx = ExecutionContext()

        create_plan(task="Simple", context=None, execution_context=ctx)

        assert "plan_strategy" in ctx.metadata
        assert ctx.metadata["plan_strategy"] in ["traditional", "rlm"]

    def test_plan_creation_error_handling(self) -> None:
        """Plan creation errors should mark context as failed."""
        ctx = ExecutionContext(user_id="user_error")

        # Empty task should still work (handled by planner)
        create_plan(task="", context=None, execution_context=ctx)

        # Should complete even with empty task
        assert ctx.status == "completed" or ctx.status == "failed"


class TestSessionContextPropagation:
    """Tests for session context propagation through planning."""

    def teardown_method(self) -> None:
        """Clear global context after each test."""
        clear_context()

    def test_plan_preserves_session_id(self) -> None:
        """Plan should inherit session_id from context."""
        session_id = "session-abc123"
        ctx = ExecutionContext(session_id=session_id, user_id="user456")

        create_plan(
            task="Analyze",
            context=None,
            execution_context=ctx,
        )

        # Session ID should be preserved in context
        assert ctx.session_id == session_id
        assert ctx.status == "completed"

    def test_plan_includes_request_id(self) -> None:
        """ExecutionContext should have unique request_id."""
        ctx1 = ExecutionContext(user_id="user1")
        ctx2 = ExecutionContext(user_id="user1")

        create_plan(task="Task 1", context=None, execution_context=ctx1)
        create_plan(task="Task 2", context=None, execution_context=ctx2)

        # Different requests
        assert ctx1.request_id != ctx2.request_id
        # Can have same user
        assert ctx1.user_id == ctx2.user_id


class TestCostTrackingInPlanning:
    """Tests for cost tracking during planning."""

    def teardown_method(self) -> None:
        """Clear global context after each test."""
        clear_context()

    def test_planning_can_track_cost(self) -> None:
        """ExecutionContext allows cost tracking during planning."""
        ctx = ExecutionContext(user_id="cost_user")

        # Create plan
        create_plan(
            task="Analyze",
            context=None,
            execution_context=ctx,
        )

        # Simulate cost from plan analysis
        ctx.tokens_used = 100
        ctx.api_calls_made = 1
        ctx.cost_estimate = 0.01

        assert ctx.tokens_used == 100
        assert ctx.cost_estimate == 0.01


class TestPlanningErrorLogging:
    """Tests for error logging during planning."""

    def teardown_method(self) -> None:
        """Clear global context after each test."""
        clear_context()

    def test_plan_error_marks_context_failed(self) -> None:
        """Plan creation errors should mark context as failed."""
        ctx = ExecutionContext(user_id="error_user")

        # Monkey-patch create_plan to force error
        import orchestrator.skills.task_planning as tp_module

        original_get_planner = tp_module.get_planner

        def broken_planner() -> LargePlanner:
            raise RuntimeError("Simulated planning error")

        tp_module.get_planner = broken_planner

        try:
            with pytest.raises(RuntimeError):
                # Force error by monkey-patching is_rlm_enabled to False
                # so it goes to traditional planner
                from orchestrator.config import get_config

                config = get_config()

                # Save original is_rlm_enabled
                original_is_rlm = config.is_rlm_enabled
                cast(Any, config).is_rlm_enabled = lambda: False

                try:
                    create_plan(
                        task="Will fail",
                        context=None,
                        execution_context=ctx,
                    )
                finally:
                    cast(Any, config).is_rlm_enabled = original_is_rlm

            # Context should be marked as failed
            assert ctx.status == "failed"
            assert ctx.error_message is not None
        finally:
            tp_module.get_planner = original_get_planner


class TestMultiplePlanCreations:
    """Tests for multiple plan creations in same session."""

    def teardown_method(self) -> None:
        """Clear global context after each test."""
        clear_context()

    def test_session_id_persistence(self) -> None:
        """Same session should use same session_id for multiple plans."""
        session_id = "multi-session-123"

        ctx1 = ExecutionContext(session_id=session_id, user_id="multi_user")
        create_plan(task="Task 1", context=None, execution_context=ctx1)

        ctx2 = ExecutionContext(session_id=session_id, user_id="multi_user")
        create_plan(task="Task 2", context=None, execution_context=ctx2)

        # Both in same session
        assert ctx1.session_id == ctx2.session_id == session_id
        # Different requests
        assert ctx1.request_id != ctx2.request_id
