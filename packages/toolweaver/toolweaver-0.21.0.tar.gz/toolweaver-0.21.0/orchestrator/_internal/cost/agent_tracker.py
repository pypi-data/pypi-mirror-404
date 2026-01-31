"""Agent-specific cost tracking and metrics.

This module provides per-agent cost tracking, metrics calculation, and
status monitoring for individual agents in the system.

Architecture:
  - AgentCostMetrics: Per-agent metric snapshots
  - AgentCostTracker: Tracks costs per agent
  - Integration with CostController for data access
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, cast


class AgentStatus(Enum):
    """Agent cost status indicators."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass
class AgentCostMetrics:
    """Metrics for a single agent's costs.

    Attributes:
        agent_name: Name of the agent
        total_calls: Number of API calls made
        total_cost_cents: Total cost in cents
        models_used: List of models used by agent
        budget_limit_cents: Budget limit in cents (None = no limit)
        spent_cents: Amount spent so far
        remaining_cents: Budget remaining (None if no budget)
        status: Current status (healthy, warning, critical, exceeded)
        calls_per_model: Breakdown of calls per model
        cost_per_model: Breakdown of costs per model
        last_call_timestamp: When last call was made
        total_cache_saves: Total tokens saved via caching
        efficiency_score: Score from 0-100 for cost efficiency
    """

    agent_name: str
    total_calls: int = 0
    total_cost_cents: float = 0.0
    models_used: list[str] = field(default_factory=list)
    budget_limit_cents: float | None = None
    spent_cents: float = 0.0
    remaining_cents: float | None = None
    status: str = "healthy"  # healthy, warning, critical, exceeded
    calls_per_model: dict[str, int] = field(default_factory=dict)
    cost_per_model: dict[str, float] = field(default_factory=dict)
    last_call_timestamp: datetime | None = None
    total_cache_saves: float = 0.0
    efficiency_score: float = 100.0

    def __post_init__(self) -> None:
        """Validate metrics."""
        if self.total_calls < 0:
            raise ValueError("total_calls must be non-negative")
        if self.total_cost_cents < 0:
            raise ValueError("total_cost_cents must be non-negative")
        if self.spent_cents < 0:
            raise ValueError("spent_cents must be non-negative")
        if not 0 <= self.efficiency_score <= 100:
            raise ValueError("efficiency_score must be between 0 and 100")
        if self.total_cache_saves < 0:
            raise ValueError("total_cache_saves must be non-negative")


class AgentCostTracker:
    """Track and analyze costs per agent.

    This class provides per-agent cost tracking with metrics calculation,
    status monitoring, and trend analysis.

    Usage:
        from orchestrator._internal.cost.integration import get_cost_controller
        from orchestrator._internal.cost.agent_tracker import AgentCostTracker

        controller = get_cost_controller()
        tracker = AgentCostTracker(controller)

        metrics = tracker.get_agent_metrics("agent1")
        print(f"Agent 1 status: {metrics.status}")
        print(f"Spent: {metrics.spent_cents}c / {metrics.budget_limit_cents}c")
    """

    # Thresholds for status determination
    WARNING_THRESHOLD = 0.75  # 75% of budget
    CRITICAL_THRESHOLD = 0.90  # 90% of budget

    def __init__(self, cost_controller: Any) -> None:
        """Initialize tracker.

        Args:
            cost_controller: CostController instance
        """
        self.cost_controller = cost_controller
        self._agent_metrics_cache: dict[str, AgentCostMetrics] = {}
        self._last_cache_update: datetime | None = None
        self._cache_ttl_seconds = 5  # Cache for 5 seconds

    def _invalidate_cache(self) -> None:
        """Invalidate metrics cache."""
        self._last_cache_update = None
        self._agent_metrics_cache.clear()

    def _should_update_cache(self) -> bool:
        """Check if cache needs updating."""
        if not self._last_cache_update:
            return True
        age_seconds = (datetime.now() - self._last_cache_update).total_seconds()
        return age_seconds > self._cache_ttl_seconds

    def _calculate_status(self, spent_cents: float, budget_cents: float | None) -> str:
        """Calculate agent status based on budget.

        Args:
            spent_cents: Amount spent
            budget_cents: Budget limit (None = no limit)

        Returns:
            Status string: healthy, warning, critical, or exceeded
        """
        if budget_cents is None:
            return AgentStatus.HEALTHY.value

        if spent_cents > budget_cents:
            return AgentStatus.EXCEEDED.value

        percentage = spent_cents / budget_cents if budget_cents > 0 else 0

        if percentage >= self.CRITICAL_THRESHOLD:
            return AgentStatus.CRITICAL.value
        elif percentage >= self.WARNING_THRESHOLD:
            return AgentStatus.WARNING.value
        else:
            return AgentStatus.HEALTHY.value

    def _calculate_efficiency_score(
        self, total_cost_cents: float, total_cache_saves: float, total_calls: int
    ) -> float:
        """Calculate efficiency score.

        Score based on cost-per-call and cache effectiveness.
        100 = highly efficient, 0 = very wasteful

        Args:
            total_cost_cents: Total cost
            total_cache_saves: Total tokens saved via cache
            total_calls: Total API calls

        Returns:
            Score from 0-100
        """
        if total_calls == 0:
            return 100.0

        cost_per_call = total_cost_cents / total_calls

        # Normalize cost per call to 0-100 scale
        # Assume average call costs 0.001 cents
        # Scores below 0.0001 cents per call = 100
        # Scores above 0.01 cents per call = 0
        if cost_per_call <= 0.0001:
            cost_score = 100.0
        elif cost_per_call >= 0.01:
            cost_score = 0.0
        else:
            # Linear scale between
            cost_score = 100.0 * (1 - (cost_per_call - 0.0001) / (0.01 - 0.0001))

        # Cache bonus: +0.5% efficiency per 1000 tokens saved
        cache_bonus = min((total_cache_saves / 1000) * 0.5, 25)

        final_score = min(100.0, cost_score + cache_bonus)
        return max(0.0, final_score)

    def get_agent_metrics(self, agent_name: str) -> AgentCostMetrics:
        """Get current metrics for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentCostMetrics with current metrics
        """
        # Get basic cost info from controller
        try:
            cost_info = self.cost_controller.cost_ledger.get_agent_costs(agent_name)
        except Exception:
            cost_info = {}

        total_cost = cost_info.get("total_cost", 0.0)
        calls = cost_info.get("calls", {})

        # Get budget status
        try:
            budget_status = self.cost_controller.get_agent_budget_status(agent_name)
            budget_limit = budget_status.get("budget_cents")
            spent = budget_status.get("total_spent_cents", 0.0)
        except Exception:
            budget_limit = None
            spent = total_cost

        # Calculate remaining
        remaining = None
        if budget_limit is not None:
            remaining = max(0.0, budget_limit - spent)

        # Get models used
        models_used = list(set(calls.keys())) if calls else []

        # Calculate per-model breakdown
        calls_per_model = calls
        cost_per_model = cost_info.get("cost_per_model", {})

        # Calculate status
        status = self._calculate_status(spent, budget_limit)

        # Get cache saves
        try:
            cache_saves = self.cost_controller.cost_ledger.get_cache_saves(agent_name)
        except Exception:
            cache_saves = 0.0

        # Calculate efficiency
        efficiency = self._calculate_efficiency_score(
            total_cost, cache_saves, len(calls) if calls else 0
        )

        # Get last call timestamp
        try:
            last_call = self.cost_controller.cost_ledger.get_last_call_timestamp(agent_name)
        except Exception:
            last_call = None

        return AgentCostMetrics(
            agent_name=agent_name,
            total_calls=len(calls) if calls else 0,
            total_cost_cents=total_cost,
            models_used=models_used,
            budget_limit_cents=budget_limit,
            spent_cents=spent,
            remaining_cents=remaining,
            status=status,
            calls_per_model=calls_per_model or {},
            cost_per_model=cost_per_model or {},
            last_call_timestamp=last_call,
            total_cache_saves=cache_saves,
            efficiency_score=efficiency,
        )

    def get_all_agent_metrics(self) -> dict[str, AgentCostMetrics]:
        """Get metrics for all tracked agents.

        Returns:
            Dictionary mapping agent names to their metrics
        """
        all_agents = self.cost_controller.get_tracked_agents()
        metrics = {}
        for agent_name in all_agents:
            try:
                metrics[agent_name] = self.get_agent_metrics(agent_name)
            except Exception:
                # Skip agents with errors
                pass
        return metrics

    def get_agents_by_status(self, status: str) -> list[str]:
        """Get list of agents with given status.

        Args:
            status: Status to filter by (healthy, warning, critical, exceeded)

        Returns:
            List of agent names with that status
        """
        all_metrics = self.get_all_agent_metrics()
        return [name for name, metrics in all_metrics.items() if metrics.status == status]

    def should_alert_agent(self, agent_name: str) -> bool:
        """Determine if agent should be alerted.

        Returns True for warning, critical, or exceeded status.

        Args:
            agent_name: Name of agent to check

        Returns:
            True if alert should be triggered
        """
        metrics = self.get_agent_metrics(agent_name)
        return metrics.status in [
            AgentStatus.WARNING.value,
            AgentStatus.CRITICAL.value,
            AgentStatus.EXCEEDED.value,
        ]

    def get_alert_reason(self, agent_name: str) -> str:
        """Get reason for alert if one exists.

        Args:
            agent_name: Name of agent

        Returns:
            Alert reason string, or empty if no alert
        """
        metrics = self.get_agent_metrics(agent_name)

        if metrics.status == AgentStatus.HEALTHY.value:
            return ""

        if metrics.budget_limit_cents is None:
            return ""

        percentage = (metrics.spent_cents / metrics.budget_limit_cents) * 100

        if metrics.status == AgentStatus.EXCEEDED.value:
            return f"Budget exceeded: {percentage:.1f}% of budget used"
        elif metrics.status == AgentStatus.CRITICAL.value:
            return f"Budget critical: {percentage:.1f}% of budget used"
        elif metrics.status == AgentStatus.WARNING.value:
            return f"Budget warning: {percentage:.1f}% of budget used"

        return ""

    def get_spending_trend(self, agent_name: str, days: int = 7) -> list[tuple[datetime, float]]:
        """Get spending trend over time.

        Args:
            agent_name: Name of agent
            days: Number of days to look back

        Returns:
            List of (timestamp, cost_cents) tuples
        """
        try:
            trend = self.cost_controller.cost_ledger.get_agent_spending_trend(agent_name, days=days)
            return cast(list[tuple[datetime, float]], trend)
        except Exception:
            return []

    def get_top_models_by_cost(self, agent_name: str, limit: int = 5) -> list[tuple[str, float]]:
        """Get most expensive models for agent.

        Args:
            agent_name: Name of agent
            limit: Maximum number of models to return

        Returns:
            List of (model_name, cost_cents) tuples sorted by cost
        """
        metrics = self.get_agent_metrics(agent_name)

        # Sort by cost descending
        sorted_models = sorted(metrics.cost_per_model.items(), key=lambda x: x[1], reverse=True)

        return sorted_models[:limit]

    def get_optimization_recommendations(self, agent_name: str) -> list[str]:
        """Get recommendations for cost optimization.

        Args:
            agent_name: Name of agent

        Returns:
            List of recommendation strings
        """
        recommendations = []
        metrics = self.get_agent_metrics(agent_name)

        # Check efficiency score
        if metrics.efficiency_score < 50:
            recommendations.append(
                f"Low efficiency score ({metrics.efficiency_score:.1f}/100): "
                "Consider using cheaper models or enabling caching"
            )

        # Check for expensive models
        top_models = self.get_top_models_by_cost(agent_name, limit=1)
        if top_models:
            model, cost = top_models[0]
            if cost > metrics.total_cost_cents * 0.5:
                recommendations.append(
                    f"Model '{model}' accounts for {(cost / metrics.total_cost_cents) * 100:.1f}% of costs: "
                    "Consider using a cheaper alternative"
                )

        # Check cache effectiveness
        if metrics.total_calls > 0 and metrics.total_cache_saves == 0:
            recommendations.append("No cache hits detected: Enable caching for repeated queries")

        # Check budget status
        if metrics.status == AgentStatus.CRITICAL.value:
            recommendations.append(
                f"Budget critical ({metrics.spent_cents}c/{metrics.budget_limit_cents}c): "
                "Reduce API calls or increase budget"
            )

        return recommendations

    def compare_agents(self, agent_names: list[str]) -> dict[str, AgentCostMetrics]:
        """Compare metrics across multiple agents.

        Args:
            agent_names: List of agent names to compare

        Returns:
            Dictionary mapping agent names to metrics
        """
        comparison = {}
        for agent_name in agent_names:
            try:
                comparison[agent_name] = self.get_agent_metrics(agent_name)
            except Exception:
                pass
        return comparison

    def get_most_expensive_agents(self, limit: int = 5) -> list[tuple[str, float]]:
        """Get most expensive agents.

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of (agent_name, cost_cents) tuples sorted by cost
        """
        all_metrics = self.get_all_agent_metrics()

        sorted_agents = sorted(
            all_metrics.items(), key=lambda x: x[1].total_cost_cents, reverse=True
        )

        return [(name, metrics.total_cost_cents) for name, metrics in sorted_agents[:limit]]

    def get_cost_distribution(self) -> dict[str, float]:
        """Get distribution of costs across agents.

        Returns:
            Dictionary mapping agent names to their cost percentage
        """
        all_metrics = self.get_all_agent_metrics()
        total_cost = sum(m.total_cost_cents for m in all_metrics.values())

        if total_cost == 0:
            return dict.fromkeys(all_metrics.keys(), 0.0)

        return {
            name: (metrics.total_cost_cents / total_cost) * 100
            for name, metrics in all_metrics.items()
        }
