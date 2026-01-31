"""
ExecutionContext for ToolWeaver - Session & Request Tracking.

Enables:
- Session tracing across multi-step workflows
- User/organization quota tracking
- Request ID correlation for observability
- Plan persistence and resumption
- Cost tracking per user/session
- Idempotent execution

Based on: Session and context management patterns from orchestrator framework.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """
    Execution context for a task/request within a session.

    Tracks session metadata, user info, and execution details.
    Enables observability, quota enforcement, and resumption.
    """

    # Session identification
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # User identification
    user_id: str | None = None
    organization_id: str | None = None

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    ended_at: datetime | None = None

    # Execution metadata
    task_description: str | None = None
    parent_request_id: str | None = None  # For nested/recursive calls

    # Idempotency
    idempotency_key: str | None = None  # For replay protection

    # Quota/cost tracking
    tokens_used: int = 0
    api_calls_made: int = 0
    cost_estimate: float = 0.0

    # Execution state
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error_message: str | None = None

    # Custom metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Results (after execution)
    result: Any | None = None

    def __post_init__(self) -> None:
        """Validate context on creation."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["ended_at"] = self.ended_at.isoformat() if self.ended_at else None
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContext":
        """Create from dictionary."""
        # Parse ISO format datetime strings
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if isinstance(data.get("ended_at"), str):
            data["ended_at"] = datetime.fromisoformat(data["ended_at"])

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionContext":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def mark_started(self) -> None:
        """Mark execution as started."""
        self.started_at = datetime.now(timezone.utc)
        self.status = "running"
        logger.info(
            "Execution started",
            extra={
                "request_id": self.request_id,
                "session_id": self.session_id,
                "user_id": self.user_id,
            },
        )

    def mark_completed(self, result: Any | None = None) -> None:
        """Mark execution as completed."""
        self.ended_at = datetime.now(timezone.utc)
        self.status = "completed"
        self.result = result
        logger.info(
            "Execution completed",
            extra={
                "request_id": self.request_id,
                "session_id": self.session_id,
                "duration_ms": (self.ended_at - self.started_at).total_seconds() * 1000
                if self.started_at
                else None,
            },
        )

    def mark_failed(self, error: str) -> None:
        """Mark execution as failed."""
        self.ended_at = datetime.now(timezone.utc)
        self.status = "failed"
        self.error_message = error
        logger.error(
            f"Execution failed: {error}",
            extra={
                "request_id": self.request_id,
                "session_id": self.session_id,
            },
        )

    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata."""
        self.metadata[key] = value

    def get_duration_ms(self) -> float | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() * 1000
        return None

    def create_child_context(self) -> "ExecutionContext":
        """Create a child context for nested execution."""
        child = ExecutionContext(
            session_id=self.session_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            parent_request_id=self.request_id,
        )
        return child


# Global execution context (thread-local in production)
_current_context: ExecutionContext | None = None


def set_context(context: ExecutionContext | None) -> None:
    """Set the current execution context."""
    global _current_context
    _current_context = context


def get_context() -> ExecutionContext | None:
    """Get the current execution context."""
    return _current_context


# Aliases for consistency
def set_execution_context(context: ExecutionContext | None) -> None:
    """Set the current execution context (alias for set_context)."""
    set_context(context)


def get_execution_context() -> ExecutionContext | None:
    """Get the current execution context (alias for get_context)."""
    return get_context()


def clear_context() -> None:
    """Clear the current execution context."""
    global _current_context
    _current_context = None
