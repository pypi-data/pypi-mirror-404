"""
Integration tests for ExecutionContext + Observability.

Tests:
- ExecutionContext logging to observability backends
- JSONL sink writing context events
- Cost tracking through observability
- Session correlation in logs
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from orchestrator.context import ExecutionContext
from orchestrator.observability import (
    JSONLSink,
    Observability,
    ObservabilityConfig,
)


class TestExecutionContextObservability:
    """Tests for ExecutionContext observability integration."""

    def test_context_logs_to_jsonl(self) -> None:
        """ExecutionContext should be loggable to JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"
            sink = JSONLSink(path)

            ctx = ExecutionContext(user_id="user123", organization_id="org456")
            ctx.task_description = "Analyze code"
            ctx.mark_started()
            ctx.tokens_used = 2000
            ctx.api_calls_made = 3
            ctx.cost_estimate = 0.15
            ctx.mark_completed(result={"analyzed": True})

            # Create observability with JSONL sink
            obs = Observability.__new__(Observability)
            obs.config = ObservabilityConfig()
            obs.sinks = [sink]  # Use direct sink

            obs.log_execution(ctx)

            # Verify
            assert path.exists()
            with open(path, encoding="utf-8") as f:
                event = json.loads(f.readline())

            assert event["session_id"] == ctx.session_id
            assert event["user_id"] == "user123"
            assert event["organization_id"] == "org456"
            assert event["status"] == "completed"
            assert event["tokens_used"] == 2000
            assert event["api_calls_made"] == 3
            assert event["cost_estimate"] == 0.15

    def test_session_tracking_in_logs(self) -> None:
        """Multiple contexts in same session should have same session_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            # Create multiple contexts in same session
            session_id = "session123"

            ctx1 = ExecutionContext(session_id=session_id, user_id="user456")
            ctx1.mark_started()
            ctx1.mark_completed()
            obs.log_execution(ctx1)

            ctx2 = ExecutionContext(session_id=session_id, user_id="user456")
            ctx2.mark_started()
            ctx2.mark_completed()
            obs.log_execution(ctx2)

            # Verify both events have same session_id
            with open(path, encoding="utf-8") as f:
                event1 = json.loads(f.readline())
                event2 = json.loads(f.readline())

            assert event1["session_id"] == session_id
            assert event2["session_id"] == session_id
            assert event1["request_id"] != event2["request_id"]  # Different requests

    def test_error_context_logs_error(self) -> None:
        """Failed execution should log error message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            ctx = ExecutionContext(user_id="user789")
            ctx.mark_started()
            ctx.mark_failed("Timeout exceeded")

            obs.log_execution(ctx)

            with open(path, encoding="utf-8") as f:
                event = json.loads(f.readline())

            assert event["status"] == "failed"
            assert event["error_message"] == "Timeout exceeded"

    def test_cost_tracking_in_logs(self) -> None:
        """Cost metrics should be preserved in logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            ctx = ExecutionContext(user_id="user111")
            ctx.tokens_used = 10000
            ctx.api_calls_made = 5
            ctx.cost_estimate = 0.50
            ctx.mark_completed()

            obs.log_execution(ctx)

            with open(path, encoding="utf-8") as f:
                event = json.loads(f.readline())

            assert event["tokens_used"] == 10000
            assert event["api_calls_made"] == 5
            assert event["cost_estimate"] == 0.50


class TestNestedContextObservability:
    """Tests for nested context logging."""

    def test_parent_child_context_logging(self) -> None:
        """Parent and child contexts should log separately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"
            sink = JSONLSink(path)

            # Create observability with direct sink
            obs = Observability.__new__(Observability)
            obs.config = ObservabilityConfig()
            obs.sinks = [sink]

            # Create parent context
            parent = ExecutionContext(user_id="user999")
            parent.add_metadata("level", "parent")
            parent.mark_completed()
            obs.log_execution(parent)

            # Create child context
            child = parent.create_child_context()
            child.add_metadata("level", "child")
            child.mark_completed()
            obs.log_execution(child)

            # Verify both logged
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2
            parent_event = json.loads(lines[0])
            child_event = json.loads(lines[1])

            # Same session, different requests
            assert parent_event["session_id"] == child_event["session_id"]
            assert parent_event["request_id"] != child_event["request_id"]
            assert child_event["parent_request_id"] == parent.request_id


class TestObservabilityMultipleSinks:
    """Tests for writing to multiple sinks."""

    def test_multiple_jsonl_logs(self) -> None:
        """Should write to multiple contexts sequentially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            # Log multiple contexts
            for i in range(5):
                ctx = ExecutionContext(user_id=f"user{i}")
                ctx.tokens_used = 1000 * (i + 1)
                ctx.mark_completed()
                obs.log_execution(ctx)

            # Verify all events logged
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 5
            for i, line in enumerate(lines):
                event = json.loads(line)
                assert event["tokens_used"] == 1000 * (i + 1)


class TestContextMetadataLogging:
    """Tests for metadata in logs."""

    def test_metadata_not_logged_directly(self) -> None:
        """Context metadata should not be in event (privacy)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            ctx = ExecutionContext(user_id="user123")
            ctx.add_metadata("api_key", "secret123")  # Should not log this
            ctx.add_metadata("internal", "data")
            ctx.mark_completed()

            obs.log_execution(ctx)

            with open(path, encoding="utf-8") as f:
                event = json.loads(f.readline())

            # Metadata should not be in event
            assert "metadata" not in event
            assert "api_key" not in str(event)


class TestTimeSeriesLogging:
    """Tests for time-series logging."""

    def test_timestamp_in_events(self) -> None:
        """All events should have timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            ctx = ExecutionContext()
            ctx.mark_completed()
            obs.log_execution(ctx)

            with open(path, encoding="utf-8") as f:
                event = json.loads(f.readline())

            assert "timestamp" in event
            # Verify it's ISO format
            datetime.fromisoformat(event["timestamp"])

    def test_duration_preserved(self) -> None:
        """Duration should be calculated and logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "execution.jsonl"

            config = ObservabilityConfig()
            config.jsonl_path = path
            config.jsonl_sink = True
            config.otlp_enabled = False
            config.wandb_enabled = False

            obs = Observability(config)

            ctx = ExecutionContext()
            ctx.mark_started()
            # Simulate some time
            ctx.ended_at = ctx.started_at  # For testing, instant completion
            ctx.status = "completed"

            obs.log_execution(ctx)

            with open(path) as f:
                event = json.loads(f.readline())

            assert event["duration_ms"] is not None
