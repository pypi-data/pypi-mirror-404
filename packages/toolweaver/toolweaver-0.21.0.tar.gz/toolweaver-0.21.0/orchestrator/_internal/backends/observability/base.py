"""
Observability Backend - Abstract Base Class

Defines the interface for logging, tracing, and monitoring.
Supports multiple observability platforms via pluggable architecture.

Phase 5: Logging, LangSmith, LangFuse, Datadog
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class ObservabilityError(Exception):
    """Raised when observability operations fail."""

    pass


class ObservabilityBackend(ABC):
    """
    Abstract base class for observability strategies.

    Handles logging, tracing, metrics, and monitoring.
    Different implementations support various observability platforms.

    Example:
        backend = get_observability_backend("logging")
        backend.log_event({"type": "completion", "model": "gpt-4"})
        backend.log_trace("trace-123", {"span": "llm_call", "duration_ms": 500})
    """

    @abstractmethod
    def log_event(self, event: dict[str, Any], **kwargs: Any) -> bool:
        """
        Log a discrete event.

        Args:
            event: Event data dictionary
            **kwargs: Implementation-specific options

        Returns:
            True if logged successfully

        Raises:
            ObservabilityError: If logging fails
        """
        pass

    @abstractmethod
    def log_trace(self, trace_id: str, span: dict[str, Any], **kwargs: Any) -> bool:
        """
        Log a trace span.

        Args:
            trace_id: Unique trace identifier
            span: Span data (name, duration, metadata)
            **kwargs: Implementation-specific options

        Returns:
            True if logged successfully

        Raises:
            ObservabilityError: If logging fails
        """
        pass

    @abstractmethod
    def log_metric(self, name: str, value: float, **kwargs: Any) -> bool:
        """
        Log a metric value.

        Args:
            name: Metric name
            value: Metric value
            **kwargs: Tags, dimensions, etc.

        Returns:
            True if logged successfully
        """
        pass

    @abstractmethod
    def query_events(self, filters: dict[str, Any] | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Query logged events.

        Args:
            filters: Filter criteria
            **kwargs: Implementation-specific query options

        Returns:
            List of matching events
        """
        pass


def get_observability_backend(backend_type: str = "logging", **kwargs: Any) -> ObservabilityBackend:
    """
    Factory function to get observability backend instance.

    Args:
        backend_type: Type of backend ("logging", "langsmith", "langfuse", "datadog")
        **kwargs: Backend-specific initialization parameters

    Returns:
        ObservabilityBackend instance

    Raises:
        ValueError: If backend_type is unknown
        ObservabilityError: If initialization fails

    Example:
        # Logging backend (default)
        backend = get_observability_backend("logging")

        # LangSmith (Phase 5)
        backend = get_observability_backend("langsmith", api_key="...")

        # Datadog (Phase 5)
        backend = get_observability_backend("datadog", api_key="...")
    """
    from .logging_backend import LoggingObservabilityBackend

    backends = {
        "logging": LoggingObservabilityBackend,
    }

    # Phase 5: Add enterprise backends
    # try:
    #     from .langsmith import LangSmithBackend
    #     backends["langsmith"] = LangSmithBackend
    # except ImportError:
    #     pass

    # try:
    #     from .langfuse import LangFuseBackend
    #     backends["langfuse"] = LangFuseBackend
    # except ImportError:
    #     pass

    # try:
    #     from .datadog import DatadogBackend
    #     backends["datadog"] = DatadogBackend
    # except ImportError:
    #     pass

    backend_class = backends.get(backend_type)
    if not backend_class:
        available = ", ".join(backends.keys())
        raise ValueError(f"Unknown backend type: {backend_type}. Available backends: {available}")

    try:
        return backend_class(**kwargs)
    except Exception as e:
        raise ObservabilityError(f"Failed to initialize {backend_type} backend: {e}") from e
