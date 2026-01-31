"""Cost alert system for budget and spending notifications.

This module provides alert generation, management, and history tracking
for cost control events.

Architecture:
  - CostAlert: Alert data structure
  - AlertManager: Manages alert lifecycle
  - Alert Types: budget_warning, budget_exceeded, high_spending
  - Alert Severity: info, warning, critical
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AlertType(Enum):
    """Types of cost alerts."""

    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    HIGH_SPENDING = "high_spending"
    THRESHOLD_REACHED = "threshold_reached"
    INEFFICIENCY_DETECTED = "inefficiency_detected"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostAlert:
    """A single cost alert.

    Attributes:
        alert_id: Unique alert identifier
        agent_name: Name of affected agent
        alert_type: Type of alert
        severity: Severity level (info, warning, critical)
        message: Human-readable message
        details: Additional details as dictionary
        timestamp: When alert was created
        acknowledged: Whether alert was acknowledged
        acknowledged_at: When alert was acknowledged
        recommended_action: Suggested action to take
        metric_value: Value that triggered alert (e.g., cost in cents)
        threshold_value: Threshold that was exceeded (if applicable)
    """

    alert_id: str
    agent_name: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    recommended_action: str = ""
    metric_value: float | None = None
    threshold_value: float | None = None

    def __post_init__(self) -> None:
        """Validate alert."""
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())

    def acknowledge(self) -> bool:
        """Acknowledge this alert.

        Returns:
            True if successfully acknowledged
        """
        if self.acknowledged:
            return False
        self.acknowledged = True
        self.acknowledged_at = datetime.now()
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary.

        Returns:
            Dictionary representation of alert
        """
        return {
            "alert_id": self.alert_id,
            "agent_name": self.agent_name,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "recommended_action": self.recommended_action,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
        }


class AlertManager:
    """Manage cost-related alerts.

    Handles creation, storage, retrieval, and acknowledgment of alerts.

    Usage:
        manager = AlertManager()
        alert = manager.create_budget_warning_alert(
            agent_name="agent1",
            current_spending=50,
            budget_limit=100,
        )
        manager.acknowledge_alert(alert.alert_id)
    """

    def __init__(self) -> None:
        """Initialize alert manager."""
        self._alerts: dict[str, CostAlert] = {}  # by alert_id
        self._agent_alerts: dict[str, list[str]] = {}  # agent_name -> [alert_ids]
        self._unacknowledged_count: dict[str, int] = {}  # agent_name -> count

    def create_alert(
        self,
        agent_name: str,
        alert_type: str | AlertType,
        severity: str,
        message: str,
        details: dict[str, Any] | None = None,
        recommended_action: str = "",
        metric_value: float | None = None,
        threshold_value: float | None = None,
    ) -> CostAlert:
        """Create a new alert.

        Args:
            agent_name: Name of affected agent
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            details: Additional details
            recommended_action: Suggested action
            metric_value: Value that triggered alert
            threshold_value: Threshold exceeded

        Returns:
            Created CostAlert
        """
        alert_id = str(uuid.uuid4())

        # Convert string to enum
        alert_type_enum = AlertType(alert_type) if isinstance(alert_type, str) else alert_type
        severity_enum = AlertSeverity(severity) if isinstance(severity, str) else severity

        alert = CostAlert(
            alert_id=alert_id,
            agent_name=agent_name,
            alert_type=alert_type_enum,
            severity=severity_enum,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            recommended_action=recommended_action,
            metric_value=metric_value,
            threshold_value=threshold_value,
        )

        self._alerts[alert_id] = alert

        # Track by agent
        if agent_name not in self._agent_alerts:
            self._agent_alerts[agent_name] = []
            self._unacknowledged_count[agent_name] = 0

        self._agent_alerts[agent_name].append(alert_id)
        self._unacknowledged_count[agent_name] += 1

        return alert

    def create_budget_warning_alert(
        self,
        agent_name: str,
        current_spending: float,
        budget_limit: float,
    ) -> CostAlert:
        """Create budget warning alert (75% of budget).

        Args:
            agent_name: Name of agent
            current_spending: Current spending in cents
            budget_limit: Budget limit in cents

        Returns:
            Created CostAlert
        """
        percentage = (current_spending / budget_limit) * 100
        return self.create_alert(
            agent_name=agent_name,
            alert_type=AlertType.BUDGET_WARNING.value,
            severity=AlertSeverity.WARNING.value,
            message=f"Budget warning for {agent_name}: {percentage:.1f}% of budget used",
            recommended_action="Monitor spending or increase budget",
            metric_value=current_spending,
            threshold_value=budget_limit * 0.75,
            details={
                "current_spending": current_spending,
                "budget_limit": budget_limit,
                "percentage": percentage,
            },
        )

    def create_budget_exceeded_alert(
        self,
        agent_name: str,
        current_spending: float,
        budget_limit: float,
    ) -> CostAlert:
        """Create budget exceeded alert.

        Args:
            agent_name: Name of agent
            current_spending: Current spending in cents
            budget_limit: Budget limit in cents

        Returns:
            Created CostAlert
        """
        percentage = (current_spending / budget_limit) * 100
        overage = current_spending - budget_limit

        return self.create_alert(
            agent_name=agent_name,
            alert_type=AlertType.BUDGET_EXCEEDED.value,
            severity=AlertSeverity.CRITICAL.value,
            message=f"Budget exceeded for {agent_name}: {percentage:.1f}% of budget used ({overage}c over)",
            recommended_action="Stop calls immediately or increase budget",
            metric_value=current_spending,
            threshold_value=budget_limit,
            details={
                "current_spending": current_spending,
                "budget_limit": budget_limit,
                "overage": overage,
                "percentage": percentage,
            },
        )

    def create_high_spending_alert(
        self,
        agent_name: str,
        current_spending: float,
        daily_average: float,
    ) -> CostAlert:
        """Create high spending alert.

        Args:
            agent_name: Name of agent
            current_spending: Current spending in cents
            daily_average: Daily average spending in cents

        Returns:
            Created CostAlert
        """
        multiplier = current_spending / daily_average if daily_average > 0 else 0

        return self.create_alert(
            agent_name=agent_name,
            alert_type=AlertType.HIGH_SPENDING.value,
            severity=AlertSeverity.WARNING.value,
            message=f"High spending for {agent_name}: {multiplier:.1f}x daily average",
            recommended_action="Review recent API calls for anomalies",
            metric_value=current_spending,
            threshold_value=daily_average * 2,  # 2x average
            details={
                "current_spending": current_spending,
                "daily_average": daily_average,
                "multiplier": multiplier,
            },
        )

    def create_inefficiency_alert(
        self,
        agent_name: str,
        efficiency_score: float,
    ) -> CostAlert:
        """Create inefficiency alert.

        Args:
            agent_name: Name of agent
            efficiency_score: Efficiency score (0-100)

        Returns:
            Created CostAlert
        """
        return self.create_alert(
            agent_name=agent_name,
            alert_type=AlertType.INEFFICIENCY_DETECTED.value,
            severity=AlertSeverity.INFO.value,
            message=f"Low efficiency detected for {agent_name}: score {efficiency_score:.1f}/100",
            recommended_action="Consider model optimization or caching",
            metric_value=efficiency_score,
            threshold_value=50.0,  # Threshold below which inefficiency detected
            details={
                "efficiency_score": efficiency_score,
            },
        )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge

        Returns:
            True if successfully acknowledged
        """
        if alert_id not in self._alerts:
            return False

        alert = self._alerts[alert_id]
        if alert.acknowledged:
            return False

        alert.acknowledge()
        agent_name = alert.agent_name
        if agent_name in self._unacknowledged_count:
            self._unacknowledged_count[agent_name] = max(
                0, self._unacknowledged_count[agent_name] - 1
            )

        return True

    def get_alert(self, alert_id: str) -> CostAlert | None:
        """Get specific alert by ID.

        Args:
            alert_id: ID of alert

        Returns:
            CostAlert or None if not found
        """
        return self._alerts.get(alert_id)

    def get_pending_alerts(self, agent_name: str) -> list[CostAlert]:
        """Get unacknowledged alerts for agent.

        Args:
            agent_name: Name of agent

        Returns:
            List of unacknowledged CostAlert objects
        """
        if agent_name not in self._agent_alerts:
            return []

        alert_ids = self._agent_alerts[agent_name]
        return [
            self._alerts[alert_id]
            for alert_id in alert_ids
            if alert_id in self._alerts and not self._alerts[alert_id].acknowledged
        ]

    def get_all_pending_alerts(self) -> list[CostAlert]:
        """Get all unacknowledged alerts.

        Returns:
            List of all pending CostAlert objects
        """
        return [alert for alert in self._alerts.values() if not alert.acknowledged]

    def get_alert_history(
        self,
        agent_name: str | None = None,
        alert_type: str | None = None,
        days: int = 30,
    ) -> list[CostAlert]:
        """Get alert history.

        Args:
            agent_name: Filter by agent (None = all)
            alert_type: Filter by type (None = all)
            days: Look back this many days

        Returns:
            List of matching CostAlert objects
        """
        cutoff = datetime.now() - __import__("datetime").timedelta(days=days)

        alerts = [alert for alert in self._alerts.values() if alert.timestamp >= cutoff]

        # Filter by agent if specified
        if agent_name:
            alerts = [a for a in alerts if a.agent_name == agent_name]

        # Filter by type if specified
        if alert_type:
            alerts = [
                a
                for a in alerts
                if a.alert_type.value == alert_type
            ]

        # Sort by timestamp descending
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts

    def get_unacknowledged_count(self, agent_name: str) -> int:
        """Get count of unacknowledged alerts for agent.

        Args:
            agent_name: Name of agent

        Returns:
            Number of unacknowledged alerts
        """
        return self._unacknowledged_count.get(agent_name, 0)

    def get_total_unacknowledged_count(self) -> int:
        """Get total count of unacknowledged alerts across all agents.

        Returns:
            Total number of unacknowledged alerts
        """
        return sum(self._unacknowledged_count.values())

    def clear_alerts_for_agent(self, agent_name: str) -> int:
        """Clear all acknowledged alerts for an agent.

        Args:
            agent_name: Name of agent

        Returns:
            Number of alerts cleared
        """
        if agent_name not in self._agent_alerts:
            return 0

        alert_ids = self._agent_alerts[agent_name].copy()
        cleared = 0

        for alert_id in alert_ids:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                if alert.acknowledged:
                    del self._alerts[alert_id]
                    self._agent_alerts[agent_name].remove(alert_id)
                    cleared += 1

        return cleared

    def get_alert_stats(self) -> dict[str, Any]:
        """Get statistics about alerts.

        Returns:
            Dictionary with alert statistics
        """
        total = len(self._alerts)
        pending = sum(1 for a in self._alerts.values() if not a.acknowledged)
        acknowledged = total - pending

        by_severity: dict[AlertSeverity, int] = {}
        by_type: dict[AlertType, int] = {}

        for alert in self._alerts.values():
            severity = alert.severity
            alert_type = alert.alert_type

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[alert_type] = by_type.get(alert_type, 0) + 1

        return {
            "total_alerts": total,
            "pending": pending,
            "acknowledged": acknowledged,
            "by_severity": {s.value: count for s, count in by_severity.items()},
            "by_type": {t.value: count for t, count in by_type.items()},
            "agents_with_alerts": len(self._agent_alerts),
        }
