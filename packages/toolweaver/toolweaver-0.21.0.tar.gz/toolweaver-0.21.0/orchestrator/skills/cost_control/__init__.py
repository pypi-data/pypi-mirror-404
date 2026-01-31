"""
Cost Control Skill

Wrapper around orchestrator._internal.cost for skills-based access.
This is a thin adapter - all implementation stays in _internal.
"""

from typing import Any, Optional

from orchestrator._internal.cost.agent_tracker import AgentCostMetrics
from orchestrator._internal.cost.alerts import CostAlert
from orchestrator._internal.cost.budget_enforcer import BudgetPolicy
from orchestrator._internal.cost.integration import (
    CostTrackingConfig,
    get_cost_controller,
)


class Skill:
    """
    Cost Control Skill following Agent Skills specification.

    This is a thin wrapper around the existing cost control implementation
    in orchestrator._internal.cost. No refactoring needed.
    """

    def __init__(self) -> None:
        """Initialize skill."""
        self.controller: Any = get_cost_controller()

    def track_api_call(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str = "openai",
    ) -> Any:
        """Track cost for an API call.

        Args:
            agent_name: Name of agent making the call
            model: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            provider: Provider name (for future use)

        Returns:
            Cost breakdown dictionary
        """
        # Note: provider parameter is accepted for API compatibility but not
        # currently used by the underlying controller
        return self.controller.track_api_call(
            agent_name=agent_name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def set_budget(
        self,
        agent_name: str,
        total_limit: float | None = None,
        daily_limit: float | None = None,
        per_request_limit: float | None = None,
    ) -> BudgetPolicy:
        """Set budget limits for an agent.

        Args:
            agent_name: Name of agent
            total_limit: Total budget limit in cents
            daily_limit: Daily budget limit in cents
            per_request_limit: Per-request limit in cents

        Returns:
            Budget policy object
        """
        policy = BudgetPolicy(name=agent_name)
        if total_limit:
            policy.total_budget_cents = total_limit
        if daily_limit:
            policy.period_budget_cents = daily_limit
        if per_request_limit:
            policy.per_operation_limit_cents = per_request_limit

        self.controller.set_budget_policy(agent_name, policy)
        return policy

    def get_agent_metrics(self, agent_name: str) -> AgentCostMetrics | None:
        """Get cost metrics for an agent.

        Args:
            agent_name: Name of agent

        Returns:
            Metrics object or None if agent not found
        """
        return self.controller.agent_tracker.get_metrics(agent_name)

    def get_alerts(self, severity: str | None = None, alert_type: str | None = None) -> Any:
        """Get active cost alerts.

        Args:
            severity: Filter by severity
            alert_type: Filter by type

        Returns:
            List of active alerts
        """
        return self.controller.alert_manager.get_active_alerts(
            severity=severity, alert_type=alert_type
        )

    def enable_tracking(self) -> bool:
        """Enable cost tracking globally.

        Returns:
            True if successful
        """
        self.controller.enable_cost_tracking()
        return True

    def disable_tracking(self) -> bool:
        """Disable cost tracking globally.

        Returns:
            True if successful
        """
        self.controller.disable_cost_tracking()
        return True

    def get_total_cost(self) -> float:
        """Get total cost across all agents.

        Returns:
            Total cost in cents
        """
        return self.controller.get_total_cost()

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive cost summary.

        Returns:
            Summary dictionary with metrics
        """
        metrics = self.controller.get_metrics()
        return {
            "total_cost_cents": metrics.total_cost,
            "total_calls": metrics.total_calls,
            "enabled": self.controller.config.enabled,
            "agent_count": len(metrics.agents_tracked),
            "alerts": len(self.get_alerts()),
        }


__all__ = ["Skill"]
