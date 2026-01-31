"""
Tests for ExecutionContext (SessionContext) implementation.

Tests:
- ExecutionContext creation and defaults
- Serialization (to/from dict/JSON)
- Status tracking (pending -> running -> completed/failed)
- Metadata management
- Duration calculation
- Child context creation (nested execution)
- Idempotency key handling
"""

import json
from datetime import datetime, timedelta

from orchestrator.context import (
    ExecutionContext,
    clear_context,
    get_context,
    set_context,
)


class TestExecutionContextCreation:
    """Tests for ExecutionContext creation and defaults."""

    def test_context_creation_defaults(self) -> None:
        """ExecutionContext should have sensible defaults."""
        ctx = ExecutionContext()

        assert ctx.session_id is not None
        assert ctx.request_id is not None
        assert ctx.user_id is None
        assert ctx.organization_id is None
        assert ctx.status == "pending"
        assert ctx.tokens_used == 0
        assert ctx.api_calls_made == 0
        assert ctx.metadata == {}

    def test_context_creation_with_user(self) -> None:
        """Should support user_id and organization_id."""
        ctx = ExecutionContext(user_id="user123", organization_id="org456")

        assert ctx.user_id == "user123"
        assert ctx.organization_id == "org456"

    def test_context_session_id_unique(self) -> None:
        """Each context should have unique session_id."""
        ctx1 = ExecutionContext()
        ctx2 = ExecutionContext()

        assert ctx1.session_id != ctx2.session_id
        assert ctx1.request_id != ctx2.request_id

    def test_context_created_at_set(self) -> None:
        """created_at should be set automatically."""
        from datetime import timezone

        before = datetime.now(timezone.utc)
        ctx = ExecutionContext()
        after = datetime.now(timezone.utc)

        assert before <= ctx.created_at <= after

    def test_context_with_parent_request_id(self) -> None:
        """Should support parent_request_id for nested calls."""
        ctx = ExecutionContext(parent_request_id="parent-123")

        assert ctx.parent_request_id == "parent-123"

    def test_context_with_idempotency_key(self) -> None:
        """Should support idempotency_key for replay protection."""
        ctx = ExecutionContext(idempotency_key="idempotent-key-456")

        assert ctx.idempotency_key == "idempotent-key-456"


class TestExecutionContextStatusTracking:
    """Tests for status tracking."""

    def test_mark_started(self) -> None:
        """mark_started should update status and timestamp."""
        ctx = ExecutionContext()

        ctx.mark_started()

        assert ctx.status == "running"
        assert ctx.started_at is not None

    def test_mark_completed(self) -> None:
        """mark_completed should update status and timestamp."""
        ctx = ExecutionContext()
        ctx.mark_started()

        ctx.mark_completed(result={"answer": 42})

        assert ctx.status == "completed"
        assert ctx.ended_at is not None
        assert ctx.result == {"answer": 42}

    def test_mark_failed(self) -> None:
        """mark_failed should update status and error message."""
        ctx = ExecutionContext()
        ctx.mark_started()

        ctx.mark_failed("Something went wrong")

        assert ctx.status == "failed"
        assert ctx.ended_at is not None
        assert ctx.error_message == "Something went wrong"

    def test_status_progression(self) -> None:
        """Status should progress: pending -> running -> completed."""
        ctx = ExecutionContext()

        assert ctx.status == "pending"

        ctx.mark_started()
        assert ctx.status == "running"

        ctx.mark_completed()
        assert ctx.status == "completed"


class TestExecutionContextDuration:
    """Tests for duration calculation."""

    def test_get_duration_ms_completed(self) -> None:
        """get_duration_ms should return duration for completed execution."""
        ctx = ExecutionContext()
        ctx.mark_started()

        # Simulate execution time
        assert ctx.started_at is not None
        ctx.ended_at = ctx.started_at + timedelta(milliseconds=100)

        duration = ctx.get_duration_ms()
        assert duration is not None
        assert 95 <= duration <= 105  # Allow some tolerance

    def test_get_duration_ms_running(self) -> None:
        """get_duration_ms should return None if still running."""
        ctx = ExecutionContext()
        ctx.mark_started()

        duration = ctx.get_duration_ms()
        assert duration is None

    def test_get_duration_ms_pending(self) -> None:
        """get_duration_ms should return None if pending."""
        ctx = ExecutionContext()

        duration = ctx.get_duration_ms()
        assert duration is None


class TestExecutionContextMetadata:
    """Tests for metadata management."""

    def test_add_metadata(self) -> None:
        """Should support adding custom metadata."""
        ctx = ExecutionContext()

        ctx.add_metadata("model", "claude-3")
        ctx.add_metadata("retry_count", 2)

        assert ctx.metadata["model"] == "claude-3"
        assert ctx.metadata["retry_count"] == 2

    def test_metadata_dict_initialization(self) -> None:
        """Should support metadata dict on creation."""
        ctx = ExecutionContext(metadata={"source": "api", "version": "v1"})

        assert ctx.metadata["source"] == "api"
        assert ctx.metadata["version"] == "v1"

    def test_multiple_metadata_updates(self) -> None:
        """Should accumulate metadata."""
        ctx = ExecutionContext()

        ctx.add_metadata("step", 1)
        ctx.add_metadata("step", 2)  # Overwrite
        ctx.add_metadata("attempts", 3)

        assert ctx.metadata["step"] == 2
        assert ctx.metadata["attempts"] == 3
        assert len(ctx.metadata) == 2


class TestExecutionContextSerialization:
    """Tests for serialization to dict and JSON."""

    def test_to_dict(self) -> None:
        """to_dict should convert context to dictionary."""
        ctx = ExecutionContext(user_id="user123", task_description="Analyze code")
        ctx.mark_started()
        ctx.mark_completed(result={"status": "ok"})

        data = ctx.to_dict()

        assert data["session_id"] == ctx.session_id
        assert data["request_id"] == ctx.request_id
        assert data["user_id"] == "user123"
        assert data["status"] == "completed"
        assert data["result"] == {"status": "ok"}
        assert isinstance(data["created_at"], str)  # ISO format
        assert isinstance(data["started_at"], str)
        assert isinstance(data["ended_at"], str)

    def test_to_json(self) -> None:
        """to_json should convert context to JSON string."""
        ctx = ExecutionContext(user_id="user123", organization_id="org456")

        json_str = ctx.to_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["user_id"] == "user123"
        assert data["organization_id"] == "org456"

    def test_from_dict(self) -> None:
        """from_dict should reconstruct context from dictionary."""
        original = ExecutionContext(user_id="user123", tokens_used=1000)
        original.mark_started()

        data = original.to_dict()
        reconstructed = ExecutionContext.from_dict(data)

        assert reconstructed.session_id == original.session_id
        assert reconstructed.user_id == original.user_id
        assert reconstructed.tokens_used == 1000
        assert reconstructed.status == "running"
        assert reconstructed.started_at == original.started_at

    def test_from_json(self) -> None:
        """from_json should reconstruct context from JSON string."""
        original = ExecutionContext(user_id="user123", organization_id="org456")

        json_str = original.to_json()
        reconstructed = ExecutionContext.from_json(json_str)

        assert reconstructed.session_id == original.session_id
        assert reconstructed.user_id == "user123"
        assert reconstructed.organization_id == "org456"

    def test_roundtrip_dict(self) -> None:
        """Roundtrip dict conversion should preserve all data."""
        original = ExecutionContext(
            user_id="user123",
            organization_id="org456",
            idempotency_key="key789",
            tokens_used=5000,
            api_calls_made=3,
            cost_estimate=0.50,
            metadata={"model": "claude-3", "retry": 2},
        )
        original.mark_started()
        original.mark_completed(result={"output": "test"})

        data = original.to_dict()
        reconstructed = ExecutionContext.from_dict(data)

        assert reconstructed.user_id == original.user_id
        assert reconstructed.organization_id == original.organization_id
        assert reconstructed.idempotency_key == original.idempotency_key
        assert reconstructed.tokens_used == 5000
        assert reconstructed.api_calls_made == 3
        assert reconstructed.cost_estimate == 0.50
        assert reconstructed.metadata == original.metadata
        assert reconstructed.result == original.result
        assert reconstructed.status == "completed"


class TestExecutionContextChildContext:
    """Tests for child context creation."""

    def test_create_child_context(self) -> None:
        """create_child_context should inherit session/user info."""
        parent = ExecutionContext(user_id="user123", organization_id="org456")

        child = parent.create_child_context()

        assert child.session_id == parent.session_id  # Same session
        assert child.request_id != parent.request_id  # Different request
        assert child.user_id == parent.user_id
        assert child.organization_id == parent.organization_id
        assert child.parent_request_id == parent.request_id

    def test_child_context_independence(self) -> None:
        """Child context should be independent for status/metadata."""
        parent = ExecutionContext(user_id="user123")
        parent.mark_started()
        parent.add_metadata("parent", True)

        child = parent.create_child_context()
        child.mark_started()
        child.add_metadata("child", True)

        assert parent.status == "running"
        assert child.status == "running"
        assert "parent" in parent.metadata
        assert "parent" not in child.metadata
        assert "child" in child.metadata
        assert "child" not in parent.metadata

    def test_nested_child_contexts(self) -> None:
        """Should support multiple levels of nesting."""
        grandparent = ExecutionContext(user_id="user123")
        parent = grandparent.create_child_context()
        child = parent.create_child_context()

        assert child.session_id == grandparent.session_id
        assert child.user_id == grandparent.user_id
        assert child.parent_request_id == parent.request_id
        assert parent.parent_request_id == grandparent.request_id


class TestExecutionContextGlobal:
    """Tests for global context management."""

    def test_set_get_context(self) -> None:
        """Should support setting and getting global context."""
        ctx = ExecutionContext(user_id="user123")

        set_context(ctx)
        retrieved = get_context()

        assert retrieved is not None
        assert retrieved.user_id == "user123"

    def test_clear_context(self) -> None:
        """Should support clearing global context."""
        ctx = ExecutionContext(user_id="user123")
        set_context(ctx)

        clear_context()
        retrieved = get_context()

        assert retrieved is None

    def test_get_context_when_not_set(self) -> None:
        """get_context should return None if not set."""
        clear_context()

        retrieved = get_context()

        assert retrieved is None


class TestExecutionContextCostTracking:
    """Tests for cost and quota tracking."""

    def test_track_tokens(self) -> None:
        """Should track tokens used."""
        ctx = ExecutionContext()

        ctx.tokens_used = 1000
        ctx.tokens_used += 500

        assert ctx.tokens_used == 1500

    def test_track_api_calls(self) -> None:
        """Should track API calls."""
        ctx = ExecutionContext()

        ctx.api_calls_made = 5
        ctx.cost_estimate = 0.25

        assert ctx.api_calls_made == 5
        assert ctx.cost_estimate == 0.25

    def test_cost_tracking_on_completion(self) -> None:
        """Should preserve cost info on completion."""
        ctx = ExecutionContext(user_id="user123")
        ctx.tokens_used = 2000
        ctx.api_calls_made = 3
        ctx.cost_estimate = 0.15

        ctx.mark_completed()

        assert ctx.tokens_used == 2000
        assert ctx.api_calls_made == 3
        assert ctx.cost_estimate == 0.15


class TestExecutionContextEdgeCases:
    """Tests for edge cases."""

    def test_context_with_none_values(self) -> None:
        """Should handle None values gracefully."""
        ctx = ExecutionContext(user_id=None, parent_request_id=None, idempotency_key=None)

        assert ctx.user_id is None
        assert ctx.parent_request_id is None
        assert ctx.idempotency_key is None

    def test_context_with_empty_metadata(self) -> None:
        """Should handle empty metadata."""
        ctx = ExecutionContext(metadata={})

        assert ctx.metadata == {}
        ctx.add_metadata("key", "value")
        assert len(ctx.metadata) == 1

    def test_context_serialization_with_complex_result(self) -> None:
        """Should serialize complex result objects."""
        complex_result = {"data": [1, 2, 3], "nested": {"a": "b"}, "list": [{"x": 1}, {"y": 2}]}
        ctx = ExecutionContext()
        ctx.mark_completed(result=complex_result)

        json_str = ctx.to_json()
        reconstructed = ExecutionContext.from_json(json_str)

        assert reconstructed.result == complex_result

    def test_task_description_long(self) -> None:
        """Should handle long task descriptions."""
        long_description = "x" * 10000
        ctx = ExecutionContext(task_description=long_description)

        assert ctx.task_description is not None
        assert len(ctx.task_description) == 10000

        # Should serialize fine
        json_str = ctx.to_json()
        reconstructed = ExecutionContext.from_json(json_str)
        assert reconstructed.task_description == long_description

