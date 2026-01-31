"""
SkillMemory: Analytics and metrics tracking for skill execution.

Provides time-series metrics storage, aggregation, and analytics for monitoring
skill performance, usage patterns, and operational health.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast

redis: Any | None = None
NoBackoff: type[Any] | None = None
Retry: type[Any] | None = None

try:
    import redis as _redis
    from redis.backoff import NoBackoff as _NoBackoff
    from redis.retry import Retry as _Retry
except ImportError:
    REDIS_AVAILABLE = False
else:
    redis = _redis
    NoBackoff = _NoBackoff
    Retry = _Retry
    REDIS_AVAILABLE = True

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked for skills."""

    EXECUTION_COUNT = "execution_count"
    ERROR_COUNT = "error_count"
    LATENCY_MS = "latency_ms"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    TOKEN_USAGE = "token_usage"
    COST_USD = "cost_usd"
    SUCCESS_RATE = "success_rate"
    CUSTOM = "custom"


class TimeWindow(Enum):
    """Time windows for metric aggregation."""

    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1mo"


@dataclass
class MetricData:
    """Individual metric data point."""

    skill_name: str
    metric_type: str
    value: float
    timestamp: str
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MetricSummary:
    """Aggregated metric summary."""

    skill_name: str
    metric_type: str
    count: int
    total: float
    average: float
    min_value: float
    max_value: float
    window: str
    start_time: str
    end_time: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SkillMemory:
    """Analytics and metrics tracking for skills using Redis."""

    # Redis key prefixes
    PREFIX_METRICS = "skill:metrics"
    PREFIX_AGGREGATES = "skill:aggregates"
    PREFIX_EVENTS = "skill:events"

    # Metric retention (in seconds)
    RETENTION_RAW = 86400  # 1 day for raw metrics
    RETENTION_HOURLY = 604800  # 1 week for hourly aggregates
    RETENTION_DAILY = 2592000  # 30 days for daily aggregates

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 1,  # Different DB from SkillState
        password: str | None = None,
        connect_timeout: float = 0.5,
    ):
        """
        Initialize SkillMemory with Redis connection.

        Reads from environment variables if host/port not provided:
        - REDIS_URL: Full Redis URL (takes precedence)
        - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD: Individual config

        Args:
            host: Redis host (defaults to env or localhost)
            port: Redis port (defaults to env or 6379)
            db: Redis database number
            password: Redis password (defaults to env)
            connect_timeout: Socket connect timeout in seconds
        """
        # Try to read from REDIS_URL first (SaaS format) only when host/port not explicitly provided
        if not REDIS_AVAILABLE:
            logger.warning("Redis is not installed. SkillMemory metrics will be disabled.")
            self.redis_client = None
            return

        redis_url = os.getenv("REDIS_URL")
        redis_password = os.getenv("REDIS_PASSWORD")

        # Initialize host with default to ensure type consistency
        self.host: str = host if host is not None else (os.getenv("REDIS_HOST") or "localhost")

        if redis_url and host is None and port is None:
            try:
                # Don't pass db when using URL (Cloud plans don't support multiple DBs)
                retry_obj = cast(Any, Retry)(cast(Any, NoBackoff)(), 1) if Retry and NoBackoff else None
                self.redis_client = cast(Any, redis).from_url(
                    redis_url,
                    password=redis_password,  # Explicitly pass password if URL doesn't include it
                    decode_responses=True,
                    socket_connect_timeout=connect_timeout,
                    socket_timeout=connect_timeout,
                    retry=retry_obj,
                )
                self.redis_client.ping()
                logger.info("Connected to Redis via REDIS_URL for metrics")
                # Preserve metadata for tests and diagnostics (don't reassign host since it's str typed)
                self.port = int(os.getenv("REDIS_PORT", "6379"))
                self.db = 1  # Store for reference, but URL takes precedence
                return
            except Exception as e:
                logger.warning(f"Failed to connect via REDIS_URL: {e}; trying host/port config")

        # Fall back to host/port/password config from env or defaults
        host_val = self.host  # Already initialized above
        port_val = port or int(os.getenv("REDIS_PORT", "6379"))
        password = password or os.getenv("REDIS_PASSWORD")

        self.port = port_val
        self.db = db

        try:
            if not redis:
                raise ImportError("redis package not installed")
            retry_obj = cast(Any, Retry)(cast(Any, NoBackoff)(), 1) if Retry and NoBackoff else None
            self.redis_client = cast(Any, redis).Redis(
                host=host_val,
                port=port_val,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=connect_timeout,
                socket_timeout=connect_timeout,
                retry=retry_obj,  # fail fast
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {host}:{port}/{db}")
        except Exception as e:
            if redis and isinstance(e, cast(Any, redis).ConnectionError):
                logger.error(f"Failed to connect to Redis for metrics: {e}")
            else:
                logger.error(f"Failed to connect to Redis for metrics: {e}")
            raise

    # ===== Metric Recording =====

    def record_metric(
        self,
        skill_name: str,
        metric_type: MetricType | str,
        value: float,
        context: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Record a metric for a skill.

        Args:
            skill_name: Name of the skill
            metric_type: Type of metric (MetricType enum or string)
            value: Metric value
            context: Optional context data
            timestamp: Optional timestamp (defaults to now)
        """
        if isinstance(metric_type, MetricType):
            metric_type = metric_type.value

        timestamp = timestamp or datetime.now()
        timestamp_str = timestamp.isoformat()

        metric = MetricData(
            skill_name=skill_name,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp_str,
            context=context,
        )

        # Store raw metric with expiration
        if not self.redis_client:
            return

        key = self._build_metric_key(skill_name, metric_type, timestamp)
        self.redis_client.setex(
            key,
            self.RETENTION_RAW,
            json.dumps(metric.to_dict()),
        )

        # Update running counters for quick access
        self._update_counters(skill_name, metric_type, value, timestamp)

        logger.debug(f"Recorded {metric_type} = {value} for {skill_name}")

    def record_execution(
        self,
        skill_name: str,
        duration_ms: float,
        success: bool,
        error: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a skill execution with multiple metrics.

        Args:
            skill_name: Name of the skill
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
            context: Optional context data
        """
        timestamp = datetime.now()

        # Record execution count
        self.record_metric(
            skill_name,
            MetricType.EXECUTION_COUNT,
            1.0,
            context,
            timestamp,
        )

        # Record latency
        self.record_metric(
            skill_name,
            MetricType.LATENCY_MS,
            duration_ms,
            context,
            timestamp,
        )

        # Record error if failed
        if not success:
            self.record_metric(
                skill_name,
                MetricType.ERROR_COUNT,
                1.0,
                {**(context or {}), "error": error},
                timestamp,
            )

        # Calculate and record success rate
        self._update_success_rate(skill_name, success)

    def record_cache_event(
        self,
        skill_name: str,
        hit: bool,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a cache hit or miss.

        Args:
            skill_name: Name of the skill
            hit: True for cache hit, False for miss
            context: Optional context data
        """
        metric_type = MetricType.CACHE_HIT if hit else MetricType.CACHE_MISS
        self.record_metric(skill_name, metric_type, 1.0, context)

    def record_cost(
        self,
        skill_name: str,
        cost_usd: float,
        tokens: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Record cost metrics for a skill execution.

        Args:
            skill_name: Name of the skill
            cost_usd: Cost in USD
            tokens: Token count (optional)
            context: Optional context data
        """
        timestamp = datetime.now()

        self.record_metric(
            skill_name,
            MetricType.COST_USD,
            cost_usd,
            context,
            timestamp,
        )

        if tokens is not None:
            self.record_metric(
                skill_name,
                MetricType.TOKEN_USAGE,
                float(tokens),
                context,
                timestamp,
            )

    def record_skill_download(self, skill_name: str) -> None:
        """
        Record a skill download event.

        Args:
            skill_name: Name of the skill being downloaded
        """
        self.record_metric(
            skill_name,
            "marketplace_download",
            1.0,
            {"event": "download"},
        )

    def record_skill_rating(
        self,
        skill_name: str,
        rating: int,
        comment: str | None = None,
    ) -> None:
        """
        Record a skill rating.

        Args:
            skill_name: Name of the skill being rated
            rating: Rating value (1-5)
            comment: Optional rating comment
        """
        self.record_metric(
            skill_name,
            "marketplace_rating",
            float(rating),
            {"event": "rating", "comment": comment},
        )

    # ===== Metric Retrieval =====

    def get_metrics(
        self,
        skill_name: str,
        metric_type: MetricType | str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[MetricData]:
        """
        Get raw metrics for a skill.

        Args:
            skill_name: Name of the skill
            metric_type: Type of metric to retrieve
            start_time: Start time (defaults to 24h ago)
            end_time: End time (defaults to now)
            limit: Maximum number of metrics to return

        Returns:
            List of MetricData objects
        """
        if not self.redis_client:
            return []

        if isinstance(metric_type, MetricType):
            metric_type = metric_type.value

        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        # Get all metric keys in time range
        pattern = f"{self.PREFIX_METRICS}:{skill_name}:{metric_type}:*"
        keys = self.redis_client.keys(pattern)

        metrics = []
        for key in keys[:limit]:
            data = self.redis_client.get(key)
            if data:
                try:
                    metric_dict = json.loads(data)
                    metric = MetricData(**metric_dict)

                    # Filter by time range
                    metric_time = datetime.fromisoformat(metric.timestamp)
                    if start_time <= metric_time <= end_time:
                        metrics.append(metric)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse metric: {e}")

        # Sort by timestamp
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        return metrics[:limit]

    def get_summary(
        self,
        skill_name: str,
        metric_type: MetricType | str,
        window: TimeWindow = TimeWindow.HOUR,
    ) -> MetricSummary | None:
        """
        Get aggregated metric summary.

        Args:
            skill_name: Name of the skill
            metric_type: Type of metric
            window: Time window for aggregation

        Returns:
            MetricSummary or None
        """
        if isinstance(metric_type, MetricType):
            metric_type = metric_type.value

        # Get metrics for the window
        now = datetime.now()
        window_duration = self._get_window_duration(window)
        start_time = now - window_duration

        metrics = self.get_metrics(skill_name, metric_type, start_time, now, limit=1000)

        if not metrics:
            return None

        values = [m.value for m in metrics]
        return MetricSummary(
            skill_name=skill_name,
            metric_type=metric_type,
            count=len(values),
            total=sum(values),
            average=sum(values) / len(values),
            min_value=min(values),
            max_value=max(values),
            window=window.value,
            start_time=start_time.isoformat(),
            end_time=now.isoformat(),
        )

    def get_all_summaries(
        self,
        skill_name: str,
        window: TimeWindow = TimeWindow.HOUR,
    ) -> dict[str, MetricSummary]:
        """
        Get summaries for all metric types.

        Args:
            skill_name: Name of the skill
            window: Time window for aggregation

        Returns:
            Dictionary of metric_type -> MetricSummary
        """
        summaries = {}
        for metric_type in MetricType:
            summary = self.get_summary(skill_name, metric_type, window)
            if summary:
                summaries[metric_type.value] = summary

        return summaries

    def get_skill_metrics(self, skill_name: str) -> dict[str, Any]:
        """
        Get aggregated metrics for a skill (API convenience method).

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with metric summaries
        """
        try:
            summaries = self.get_all_summaries(skill_name, TimeWindow.DAY)
            if not summaries:
                return {"skill_name": skill_name, "metrics": {}}

            # Convert MetricSummary objects to dicts
            metrics_dict = {}
            for metric_type, summary in summaries.items():
                metrics_dict[metric_type] = summary.to_dict()

            return {"skill_name": skill_name, "metrics": metrics_dict}
        except Exception as e:
            logger.warning(f"Failed to get metrics for {skill_name}: {e}")
            return {"skill_name": skill_name, "metrics": {}, "error": str(e)}

    def get_metrics_history(self, skill_name: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get historical metrics for a skill.

        Args:
            skill_name: Name of the skill
            limit: Maximum number of records to return (default: 100, max: 1000)

        Returns:
            List of metric dictionaries with timestamp and values
        """
        if not self.redis_client:
            return []

        # Clamp limit to reasonable range
        limit = min(max(limit, 1), 1000)

        try:
            # Get all metric keys for the skill, sorted by timestamp
            pattern = f"{self.PREFIX_METRICS}:{skill_name}:*"
            keys = self.redis_client.keys(pattern)

            history = []
            for key in sorted(keys, reverse=True)[:limit]:
                value = self.redis_client.get(key)
                if value:
                    try:
                        metric_data = json.loads(value)
                        history.append(metric_data)
                    except json.JSONDecodeError:
                        pass

            # Sort by timestamp descending (most recent first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return history
        except Exception as e:
            logger.error(f"Failed to retrieve metrics history for {skill_name}: {e}")
            return []

    def get_leaderboard(
        self,
        metric_type: MetricType | str,
        limit: int = 10,
        window: TimeWindow = TimeWindow.DAY,
    ) -> list[dict[str, Any]]:
        """
        Get top skills by metric.

        Args:
            metric_type: Metric to rank by
            limit: Number of skills to return
            window: Time window

        Returns:
            List of skill rankings
        """
        if not self.redis_client:
            return []

        if isinstance(metric_type, MetricType):
            metric_type = metric_type.value

        # Get all skills that have this metric
        pattern = f"{self.PREFIX_METRICS}:*:{metric_type}:*"
        keys = self.redis_client.keys(pattern)

        # Extract unique skill names
        skill_names = set()
        for key in keys:
            parts = key.split(":")
            if len(parts) >= 3:
                skill_names.add(parts[2])

        # Get summaries for each skill
        rankings = []
        for skill_name in skill_names:
            summary = self.get_summary(skill_name, metric_type, window)
            if summary:
                rankings.append(
                    {
                        "skill_name": skill_name,
                        "total": summary.total,
                        "average": summary.average,
                        "count": summary.count,
                    }
                )

        # Sort by total (descending)
        rankings.sort(key=lambda x: x["total"], reverse=True)
        return rankings[:limit]

    # ===== Counter Operations =====

    def _update_counters(
        self,
        skill_name: str,
        metric_type: str,
        value: float,
        timestamp: datetime,
    ) -> None:
        """Update running counters for quick access."""
        if not self.redis_client:
            return

        # Hourly counter
        hour_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:{metric_type}:hourly:{timestamp.strftime('%Y%m%d%H')}"
        self.redis_client.incrbyfloat(hour_key, value)
        self.redis_client.expire(hour_key, self.RETENTION_HOURLY)

        # Daily counter
        day_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:{metric_type}:daily:{timestamp.strftime('%Y%m%d')}"
        self.redis_client.incrbyfloat(day_key, value)
        self.redis_client.expire(day_key, self.RETENTION_DAILY)

    def _update_success_rate(self, skill_name: str, success: bool) -> None:
        """Update success rate counter."""
        if not self.redis_client:
            return

        now = datetime.now()
        day_str = now.strftime("%Y%m%d")

        success_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:success:daily:{day_str}"
        total_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:total:daily:{day_str}"

        if success:
            self.redis_client.incr(success_key)
        self.redis_client.incr(total_key)

        self.redis_client.expire(success_key, self.RETENTION_DAILY)
        self.redis_client.expire(total_key, self.RETENTION_DAILY)

    def get_success_rate(
        self,
        skill_name: str,
        window: TimeWindow = TimeWindow.DAY,
    ) -> float | None:
        """
        Get success rate for a skill.

        Args:
            skill_name: Name of the skill
            window: Time window

        Returns:
            Success rate (0.0 to 1.0) or None
        """
        if not self.redis_client:
            return None

        now = datetime.now()
        day_str = now.strftime("%Y%m%d")

        success_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:success:daily:{day_str}"
        total_key = f"{self.PREFIX_AGGREGATES}:{skill_name}:total:daily:{day_str}"

        success = self.redis_client.get(success_key)
        total = self.redis_client.get(total_key)

        if not total or int(total) == 0:
            return None

        return float(success or 0) / float(total)

    # ===== Event Tracking =====

    def record_event(
        self,
        skill_name: str,
        event_type: str,
        data: dict[str, Any],
        ttl: int = 86400,
    ) -> None:
        """
        Record a skill event (errors, warnings, etc.).

        Args:
            skill_name: Name of the skill
            event_type: Type of event
            data: Event data
            ttl: Time-to-live in seconds
        """
        if not self.redis_client:
            return

        timestamp = datetime.now()
        event = {
            "skill_name": skill_name,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp.isoformat(),
        }

        key = f"{self.PREFIX_EVENTS}:{skill_name}:{event_type}:{timestamp.strftime('%Y%m%d%H%M%S')}"
        self.redis_client.setex(key, ttl, json.dumps(event))

    def get_events(
        self,
        skill_name: str,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get recent events for a skill.

        Args:
            skill_name: Name of the skill
            event_type: Optional event type filter
            limit: Maximum events to return

        Returns:
            List of events
        """
        if not self.redis_client:
            return []

        pattern = f"{self.PREFIX_EVENTS}:{skill_name}:{event_type or '*'}:*"
        keys = self.redis_client.keys(pattern)

        events = []
        for key in keys[:limit]:
            data = self.redis_client.get(key)
            if data:
                try:
                    events.append(json.loads(data))
                except json.JSONDecodeError:
                    pass

        # Sort by timestamp descending
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return events[:limit]

    # ===== Utility Methods =====

    @staticmethod
    def _build_metric_key(
        skill_name: str,
        metric_type: str,
        timestamp: datetime,
    ) -> str:
        """Build a Redis key for a metric."""
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S%f")
        return f"skill:metrics:{skill_name}:{metric_type}:{timestamp_str}"

    @staticmethod
    def _get_window_duration(window: TimeWindow) -> timedelta:
        """Get timedelta for a time window."""
        durations = {
            TimeWindow.MINUTE: timedelta(minutes=1),
            TimeWindow.HOUR: timedelta(hours=1),
            TimeWindow.DAY: timedelta(days=1),
            TimeWindow.WEEK: timedelta(weeks=1),
            TimeWindow.MONTH: timedelta(days=30),
        }
        return durations.get(window, timedelta(hours=1))

    def clear_metrics(
        self,
        skill_name: str,
        metric_type: str | None = None,
    ) -> int:
        """
        Clear metrics for a skill.

        Args:
            skill_name: Name of the skill
            metric_type: Optional metric type (clears all if None)

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        pattern = f"{self.PREFIX_METRICS}:{skill_name}:{metric_type or '*'}:*"
        keys = self.redis_client.keys(pattern)

        if keys:
            return self.redis_client.delete(*keys)
        return 0

    def health_check(self) -> dict[str, Any]:
        if not self.redis_client:
            return {
                "status": "disabled",
                "connected": False,
                "reason": "Redis not available"
            }

        """
        Get Redis connection health for metrics.

        Returns:
            Health status dictionary
        """
        try:
            info = self.redis_client.info()

            # Count total metrics
            metric_keys = self.redis_client.keys(f"{self.PREFIX_METRICS}:*")

            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version"),
                "total_metrics": len(metric_keys),
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }
