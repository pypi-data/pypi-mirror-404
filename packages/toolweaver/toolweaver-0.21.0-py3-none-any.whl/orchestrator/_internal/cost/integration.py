"""Cost system orchestrator integration.

This module integrates the cost control components with the orchestrator,
providing automatic cost tracking for all orchestrated operations.

Integration Points:
  - TokenCounter: Counts tokens in API calls
  - CostCalculator: Calculates costs from tokens
  - BudgetEnforcer: Enforces budget constraints
  - CostLedger: Records all transactions

Architecture:
  - CostController: Orchestrates cost tracking
  - Integration with ExecutionTracker for metrics
  - Hooks into message routing for automatic tracking
  - Per-agent cost tracking via agent profiles
"""

from dataclasses import dataclass
from typing import Any

from orchestrator._internal.cost.budget_enforcer import (
    BudgetEnforcer,
    BudgetExceededError,
    BudgetPolicy,
)
from orchestrator._internal.cost.cost_calculator import CostCalculator
from orchestrator._internal.cost.cost_ledger import CostLedger, Transaction, TransactionType
from orchestrator._internal.cost.token_counter import TokenCounter


@dataclass
class CostTrackingConfig:
    """Configuration for cost tracking.

    Attributes:
        enabled: Whether cost tracking is enabled
        track_by_agent: Track costs per agent
        track_by_model: Track costs per model
        track_by_operation: Track costs per operation type
        enforce_budgets: Enforce budget limits
        auto_log: Automatically log transactions
    """

    enabled: bool = True
    track_by_agent: bool = True
    track_by_model: bool = True
    track_by_operation: bool = True
    enforce_budgets: bool = True
    auto_log: bool = True


class CostController:
    """Orchestrator integration for cost control.

    This class manages all cost tracking for orchestrated operations,
    providing integration between the cost control system and the main
    orchestrator.

    Usage:
        controller = CostController()

        # Configure tracking
        controller.enable_cost_tracking()

        # Set budget for agent
        controller.set_agent_budget("agent1", total_cents=10000, period_cents=2000)

        # Track API call
        controller.track_api_call(
            agent_name="agent1",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )
    """

    def __init__(self, config: CostTrackingConfig | None = None):
        """Initialize cost controller.

        Args:
            config: CostTrackingConfig (optional, uses defaults if not provided)
        """
        self.config = config or CostTrackingConfig()

        # Core components
        self.token_counter = TokenCounter()
        self.cost_calculator = CostCalculator()
        self.budget_enforcer = BudgetEnforcer()
        self.ledger = CostLedger()

        # Tracking state
        self._agent_costs: dict[str, float] = {}
        self._operation_costs: dict[str, float] = {}
        self._enabled = False

    def enable_cost_tracking(self) -> bool:
        """Enable cost tracking.

        Returns:
            True if enabled successfully
        """
        if not self.config.enabled:
            return False

        self._enabled = True
        return True

    def disable_cost_tracking(self) -> bool:
        """Disable cost tracking.

        Returns:
            True if disabled successfully
        """
        self._enabled = False
        return True

    def disable_tracking(self) -> bool:
        """Alias for disable_cost_tracking.

        Returns:
            True if disabled successfully
        """
        return self.disable_cost_tracking()

    def is_tracking_enabled(self) -> bool:
        """Check if cost tracking is enabled.

        Returns:
            True if tracking is enabled
        """
        return self._enabled and self.config.enabled

    def set_agent_budget(
        self,
        agent_name: str,
        total_cents: float | None = None,
        period_cents: float | None = None,
        per_operation_cents: float | None = None,
    ) -> bool:
        """Set budget policy for an agent.

        Args:
            agent_name: Name of the agent
            total_cents: Total budget in cents (None = unlimited)
            period_cents: Daily budget in cents (None = unlimited)
            per_operation_cents: Per-operation limit in cents (None = unlimited)

        Returns:
            True if policy was set
        """
        if not agent_name:
            return False

        policy = BudgetPolicy(
            name=agent_name,
            total_budget_cents=total_cents,
            period_budget_cents=period_cents,
            per_operation_limit_cents=per_operation_cents,
        )

        self.budget_enforcer.set_policy(policy)
        return True

    def track_api_call(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int = 0,
        description: str = "",
    ) -> dict[str, Any]:
        """Track an API call.

        Args:
            agent_name: Name of agent making the call
            model: Model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens (default: 0)
            description: Optional description of the operation

        Returns:
            Dict with tracking results (cost, status, etc.)

        Raises:
            BudgetExceededError: If operation would exceed budget
        """
        if not self.is_tracking_enabled():
            return {"status": "tracking_disabled"}

        # Calculate cost
        breakdown = self.cost_calculator.calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        cost_cents = breakdown.total_cost

        # Check budget if enabled and policy exists
        if self.config.enforce_budgets and agent_name:
            try:
                self.budget_enforcer.check_budget(agent_name, cost_cents=cost_cents)
            except (BudgetExceededError, ValueError):
                # Re-raise BudgetExceededError, pass on ValueError (no policy)
                try:
                    self.budget_enforcer.check_budget(agent_name, cost_cents=cost_cents)
                except ValueError:
                    # No policy for this agent, skip budget check
                    pass
                except BudgetExceededError:
                    raise

        # Record spending if budget check passed and policy exists
        status = None
        if self.config.enforce_budgets and agent_name:
            try:
                status = self.budget_enforcer.record_spending(agent_name, cost_cents=cost_cents)
            except ValueError:
                # No policy for this agent
                pass

        # Log transaction if enabled
        if self.config.auto_log:
            transaction = Transaction(
                policy_name=agent_name or "unknown",
                type=TransactionType.API_CALL,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_cents=cost_cents,
                description=description,
            )
            self.ledger.record_transaction(transaction)

        # Track for metrics
        if self.config.track_by_agent and agent_name:
            self._agent_costs[agent_name] = self._agent_costs.get(agent_name, 0.0) + cost_cents

        return {
            "status": "success",
            "cost_cents": cost_cents,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "budget_status": status,
            "description": description,
        }

    def track_cache_hit(
        self,
        agent_name: str,
        model: str,
        saved_tokens: int,
        description: str = "",
    ) -> dict[str, Any]:
        """Track a cache hit (cost savings).

        Args:
            agent_name: Name of agent
            model: Model that was cached
            saved_tokens: Number of tokens saved
            description: Optional description

        Returns:
            Dict with tracking results
        """
        if not self.is_tracking_enabled():
            return {"status": "tracking_disabled"}

        # Calculate cost savings
        pricing = self.cost_calculator.get_pricing(model)
        if pricing:
            saved_cost = (saved_tokens / 1000.0) * pricing.input_price_per_1k
        else:
            saved_cost = 0.0

        # Log transaction (negative cost = savings)
        if self.config.auto_log:
            transaction = Transaction(
                policy_name=agent_name or "unknown",
                type=TransactionType.CACHE_HIT,
                model=model,
                prompt_tokens=saved_tokens,
                completion_tokens=0,
                cost_cents=-saved_cost,  # Negative for savings
                description=description or f"Cache hit saved {saved_tokens} tokens",
            )
            self.ledger.record_transaction(transaction)

        return {
            "status": "success",
            "saved_cost_cents": saved_cost,
            "saved_tokens": saved_tokens,
            "model": model,
            "description": description,
        }

    def get_agent_cost(self, agent_name: str) -> float:
        """Get total cost for an agent.

        Args:
            agent_name: Name of agent

        Returns:
            Total cost in cents
        """
        return self._agent_costs.get(agent_name, 0.0)

    def get_agent_budget_status(self, agent_name: str) -> dict[str, Any] | None:
        """Get budget status for an agent.

        Args:
            agent_name: Name of agent

        Returns:
            Dict with budget status or None if not tracked
        """
        if not self.config.enforce_budgets:
            return None

        try:
            status = self.budget_enforcer.get_status(agent_name)
            return {
                "policy_name": status.policy_name,
                "total_spent_cents": status.total_spent_cents,
                "remaining_total_cents": status.remaining_total_cents,
                "period_spent_cents": status.period_spent_cents,
                "remaining_period_cents": status.remaining_period_cents,
                "can_spend": status.can_spend,
            }
        except ValueError:
            return None

    def get_all_agent_costs(self) -> dict[str, float]:
        """Get costs for all agents.

        Returns:
            Dict of agent names to total costs
        """
        return dict(self._agent_costs)

    def get_cost_summary(self, agent_name: str | None = None) -> dict[str, Any]:
        """Get cost summary.

        Args:
            agent_name: Optional agent name to filter by

        Returns:
            Dict with cost summary
        """
        summary = self.ledger.get_cost_summary(policy_name=agent_name)

        return {
            "agent": agent_name or "all",
            "total_cost_cents": summary.total_cost_cents,
            "transaction_count": summary.transaction_count,
            "average_cost_cents": summary.average_cost_cents,
            "model_breakdown": summary.model_breakdown,
            "type_breakdown": summary.type_breakdown,
        }

    def get_tracked_models(self) -> list[str]:
        """Get list of models with transactions.

        Returns:
            List of model names
        """
        return self.ledger.get_all_models()

    def get_tracked_agents(self) -> list[str]:
        """Get list of agents with costs.

        Returns:
            List of agent names
        """
        return self.ledger.get_all_policies()

    def reset_tracking(self) -> bool:
        """Reset all tracking data.

        Returns:
            True if reset successfully
        """
        self._agent_costs.clear()
        self._operation_costs.clear()
        self.ledger.clear_transactions()
        return True

    def get_config(self) -> CostTrackingConfig:
        """Get current configuration.

        Returns:
            CostTrackingConfig
        """
        return self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update configuration.

        Args:
            **kwargs: Fields to update (enabled, track_by_agent, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# Global cost controller instance
_cost_controller: CostController | None = None


def get_cost_controller(config: CostTrackingConfig | None = None) -> CostController:
    """Get or create global cost controller.

    Args:
        config: Optional config for initialization

    Returns:
        Global CostController instance
    """
    global _cost_controller

    if _cost_controller is None:
        _cost_controller = CostController(config)
    elif config is not None:
        _cost_controller.config = config

    return _cost_controller


def reset_cost_controller() -> None:
    """Reset global cost controller."""
    global _cost_controller
    _cost_controller = None
