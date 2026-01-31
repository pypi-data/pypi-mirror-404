"""
Logging-Based Observability Backend

Simple observability using Python's logging module.
Default implementation with zero dependencies.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import ObservabilityBackend

logger = logging.getLogger(__name__)


class LoggingObservabilityBackend(ObservabilityBackend):
    """
    Observability backend using Python logging.

    Logs events, traces, and metrics to standard logging output.
    Simple, zero-dependency solution for basic observability.

    Example:
        backend = LoggingObservabilityBackend(log_level="INFO")
        backend.log_event({"type": "completion", "tokens": 150})
        backend.log_trace("trace-123", {"span": "llm_call", "duration_ms": 500})
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """
        Initialize logging backend.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger("toolweaver.observability")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        logger.info(f"Initialized LoggingObservabilityBackend with level: {log_level}")

    def log_event(self, event: dict[str, Any], **kwargs: Any) -> bool:
        """Log event as JSON to logger."""
        try:
            event_data = {"timestamp": datetime.now(timezone.utc).isoformat(), "type": "event", **event}
            self.logger.info(f"EVENT: {json.dumps(event_data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False

    def log_trace(self, trace_id: str, span: dict[str, Any], **kwargs: Any) -> bool:
        """Log trace span as JSON to logger."""
        try:
            trace_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "trace",
                "trace_id": trace_id,
                **span,
            }
            self.logger.info(f"TRACE: {json.dumps(trace_data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to log trace: {e}")
            return False

    def log_metric(self, name: str, value: float, **kwargs: Any) -> bool:
        """Log metric as JSON to logger."""
        try:
            metric_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "metric",
                "name": name,
                "value": value,
                **kwargs,
            }
            self.logger.info(f"METRIC: {json.dumps(metric_data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to log metric: {e}")
            return False

    def query_events(self, filters: dict[str, Any] | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Query not supported in logging backend.

        Logs are write-only. Use external log aggregation tools
        (like ELK, Splunk) for querying.
        """
        logger.warning("Query not supported in LoggingObservabilityBackend")
        return []

    def __repr__(self) -> str:
        return f"LoggingObservabilityBackend(level={self.logger.level})"
