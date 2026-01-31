"""
Observability integration for ToolWeaver.

Provides:
- Request/session logging (JSONL sink with rotation)
- Optional OTLP export
- Optional WANDB integration
- PII redaction (integration point)
- Cost/quota tracking
- Performance metrics

Gate: OBSERVABILITY_ENABLED environment variable
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestrator._internal.observability.redaction import redact_data
from orchestrator.observability_jsonl_sink import JSONLSinkWithRotation

logger = logging.getLogger(__name__)


@dataclass
class ToolCallMetric:
    """Single tool call metric for analysis."""

    timestamp: str
    tool_name: str
    success: bool
    latency: float
    error: str | None = None
    execution_id: str | None = None


class ObservabilityConfig:
    """Configuration for observability backends."""

    def __init__(self) -> None:
        self.enabled = os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "true"
        self.jsonl_sink = os.getenv("OBSERVABILITY_JSONL_SINK", "true").lower() == "true"
        self.otlp_enabled = os.getenv("OBSERVABILITY_OTLP_ENABLED", "false").lower() == "true"
        self.wandb_enabled = os.getenv("WANDB_ENABLED", "false").lower() == "true"
        self.redaction_enabled = os.getenv("REDACTION_ENABLED", "false").lower() == "true"

        # Output paths
        self.jsonl_path = Path(
            os.getenv("OBSERVABILITY_JSONL_PATH", ".toolweaver/observability.jsonl")
        )

        # OTLP configuration (if enabled)
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        # WANDB configuration (if enabled)
        self.wandb_project = os.getenv("WANDB_PROJECT", "toolweaver")

        logger.info(
            f"Observability config loaded: "
            f"enabled={self.enabled}, "
            f"jsonl={self.jsonl_sink}, "
            f"otlp={self.otlp_enabled}, "
            f"wandb={self.wandb_enabled}"
        )


class ObservabilitySink:
    """Base class for observability sinks."""

    def write(self, event: dict[str, Any]) -> None:
        """Write an observability event."""
        raise NotImplementedError


class JSONLSink(ObservabilitySink):
    """JSONL file sink for observability events with rotation."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.sink = JSONLSinkWithRotation(
            path=self.path,
            max_size_mb=int(os.getenv("OBSERVABILITY_JSONL_MAX_SIZE_MB", "100")),
            max_files=int(os.getenv("OBSERVABILITY_JSONL_MAX_FILES", "10")),
            compress=os.getenv("OBSERVABILITY_JSONL_COMPRESS", "true").lower() == "true",
        )

    def write(self, event: dict[str, Any]) -> None:
        """Append event to JSONL file."""
        self.sink.write(event)

    def get_stats(self) -> dict[str, Any]:
        """Get sink statistics."""
        return self.sink.get_stats()


class OTLPSink(ObservabilitySink):
    """OTLP (OpenTelemetry) sink for observability events."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._init_otlp()

    def _init_otlp(self) -> None:
        """Initialize OTLP exporter."""
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

            # Create exporter
            exporter = OTLPMetricExporter(endpoint=self.endpoint)
            reader = PeriodicExportingMetricReader(exporter)
            self.meter_provider = MeterProvider(metric_readers=[reader])
            self.meter = self.meter_provider.get_meter(__name__)

            logger.info(f"OTLP sink initialized: {self.endpoint}")
        except ImportError:
            logger.warning("OpenTelemetry not installed; OTLP sink unavailable")
            self.meter_provider = None
            self.meter = None

    def write(self, event: dict[str, Any]) -> None:
        """Export event to OTLP."""
        if self.meter is None:
            return

        try:
            # Record metrics from event
            if "duration_ms" in event and self.meter:
                counter = self.meter.create_histogram("execution.duration_ms")
                counter.record(event["duration_ms"])

            if "tokens_used" in event and self.meter:
                counter = self.meter.create_counter("tokens.used")
                counter.add(event["tokens_used"])
        except Exception as e:
            logger.error(f"Failed to write to OTLP sink: {e}")


class WANDBSink(ObservabilitySink):
    """WANDB (Weights & Biases) sink for observability events."""

    def __init__(self, project: str):
        self.project = project
        self._init_wandb()

    def _init_wandb(self) -> None:
        """Initialize WANDB."""
        try:
            import wandb as _wandb

            _wandb.init(project=self.project, reinit=True)
            self.wandb: Any = _wandb
            logger.info(f"WANDB sink initialized: {self.project}")
        except ImportError:
            logger.warning("wandb not installed; WANDB sink unavailable")
            self.wandb = None

    def write(self, event: dict[str, Any]) -> None:
        """Log event to WANDB."""
        if self.wandb is None:
            return

        try:
            # Extract key metrics
            metrics = {}
            for key in ["duration_ms", "tokens_used", "api_calls_made", "cost_estimate"]:
                if key in event:
                    metrics[key] = event[key]

            if metrics:
                self.wandb.log(metrics)
        except Exception as e:
            logger.error(f"Failed to write to WANDB sink: {e}")


class Observability:
    """Central observability manager."""

    def __init__(self, config: ObservabilityConfig | None = None):
        self.config = config or ObservabilityConfig()
        self.sinks: list[ObservabilitySink] = []

        if not self.config.enabled:
            logger.info("Observability disabled")
            return

        # Initialize sinks
        if self.config.jsonl_sink:
            self.sinks.append(JSONLSink(self.config.jsonl_path))

        if self.config.otlp_enabled:
            self.sinks.append(OTLPSink(self.config.otlp_endpoint))

        if self.config.wandb_enabled:
            self.sinks.append(WANDBSink(self.config.wandb_project))

        logger.info(f"Observability initialized with {len(self.sinks)} sinks")

    def record_tool_execution(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
        error: str | None = None,
        execution_context: Any | None = None,
        execution_id: str | None = None,
    ) -> None:
        """
        Record a tool execution event.

        Args:
            tool_name: Name of the tool called.
            success: Whether the execution was successful.
            latency_ms: Duration in milliseconds.
            error: Error message if failed.
            execution_context: Optional execution context for correlation.
            execution_id: Optional unique ID for this execution.
        """
        if not self.config.enabled:
            return

        event = {
            "event_type": "tool_execution",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "success": success,
            "duration_ms": latency_ms,
            "error_message": error,
            "execution_id": execution_id,
        }

        # Add context fields if available
        if execution_context:
            event["session_id"] = getattr(execution_context, "session_id", None)
            event["request_id"] = getattr(execution_context, "request_id", None)
            event["user_id"] = getattr(execution_context, "user_id", None)

        # Apply redaction if enabled
        if self.config.redaction_enabled:
            event = redact_data(event)

        self.log_event(event)

    def log_execution(self, context: Any) -> None:
        """Log execution context."""
        if not self.config.enabled or not context:
            return

        try:
            # Convert context to event
            event = self._context_to_event(context)

            # Write to all sinks
            self.log_event(event)
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    def log_event(self, event: dict[str, Any]) -> None:
        """Log arbitrary event dictionary to all sinks."""
        if not self.config.enabled:
            return

        try:
            # Timestamp if missing
            if "timestamp" not in event:
                event["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Apply redaction if enabled
            if self.config.redaction_enabled:
                event = self._redact_event(event)

            # Write to all sinks
            for sink in self.sinks:
                sink.write(event)
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def get_sink_stats(self) -> dict[str, Any]:
        """Get statistics from all sinks."""
        stats = {}
        for i, sink in enumerate(self.sinks):
            sink_name = sink.__class__.__name__
            if hasattr(sink, "get_stats"):
                try:
                    stats[f"{sink_name}_{i}"] = sink.get_stats()
                except Exception as e:
                    logger.error(f"Failed to get {sink_name} stats: {e}")
                    stats[f"{sink_name}_{i}"] = {"error": str(e)}
        return stats

    def _context_to_event(self, context: Any) -> dict[str, Any]:
        """Convert ExecutionContext to observability event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": getattr(context, "session_id", None),
            "request_id": getattr(context, "request_id", None),
            "parent_request_id": getattr(context, "parent_request_id", None),
            "user_id": getattr(context, "user_id", None),
            "organization_id": getattr(context, "organization_id", None),
            "status": getattr(context, "status", None),
            "duration_ms": context.get_duration_ms()
            if hasattr(context, "get_duration_ms")
            else None,
            "tokens_used": getattr(context, "tokens_used", 0),
            "api_calls_made": getattr(context, "api_calls_made", 0),
            "cost_estimate": getattr(context, "cost_estimate", 0.0),
            "error_message": getattr(context, "error_message", None),
        }

        # Apply redaction if enabled
        if self.config.redaction_enabled:
            event = self._redact_event(event)

        return event

    def _redact_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive data from event."""
        # Placeholder: actual redaction logic would go here
        # (emails, API keys, tokens, etc.)
        return event


# Global observability instance
_observability: Observability | None = None


def get_observability() -> Observability:
    """Get or initialize global observability instance."""
    global _observability
    if _observability is None:
        _observability = Observability()
    return _observability


def log_execution(context: Any) -> None:
    """Log execution context to observability backends."""
    observability = get_observability()
    observability.log_execution(context)


class MonitoringHooks:
    """
    Hooks for monitoring AgenticExecutor performance.
    Phase 5.5.4: Provides visibility into the "Think Layer".
    """

    @staticmethod
    def record_agent_start(task: str, session_id: str | None = None) -> None:
        """Record start of agentic task."""
        get_observability().log_event(
            {
                "event_type": "agent_start",
                "task_snippet": task[:100],
                "session_id": session_id,
            }
        )

    @staticmethod
    def record_agent_step(
        iteration: int, step_type: str, details: dict[str, Any] | None = None
    ) -> None:
        """
        Record agent step execution.

        Args:
            iteration: Current loop iteration
            step_type: 'plan', 'execution', 'reflection'
            details: Optional details about the step
        """
        event = {
            "event_type": "agent_step",
            "iteration": iteration,
            "step_type": step_type,
        }
        if details:
            event.update(details)
        get_observability().log_event(event)

    @staticmethod
    def record_tool_call(
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record tool execution metrics."""
        event = {
            "event_type": "tool_execution",
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
        }
        if error:
            event["error"] = error
        get_observability().log_event(event)

    @staticmethod
    def record_agent_completion(
        success: bool,
        iterations: int,
        duration_ms: float,
        total_tokens: int = 0,
        error: str | None = None,
    ) -> None:
        """Record agent task completion."""
        event = {
            "event_type": "agent_completion",
            "success": success,
            "iterations": iterations,
            "duration_ms": duration_ms,
            "total_tokens": total_tokens,
        }
        if error:
            event["error"] = error
        get_observability().log_event(event)
