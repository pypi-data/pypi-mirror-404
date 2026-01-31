"""Budget enforcement for LLM applications.

This module provides budget tracking and enforcement, preventing overspending
on LLM API calls.

Budget Models:
  - Total budget (overall limit)
  - Per-period budget (daily, weekly, monthly)
  - Per-agent budget (limit per agent)
  - Per-operation budget (limit per operation type)

Architecture:
  - BudgetPolicy: Defines budget constraints
  - BudgetEnforcer: Enforces budget constraints
  - Integration with CostLedger for tracking
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class BudgetPeriod(Enum):
    """Budget reset periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    UNLIMITED = "unlimited"


class BudgetExceededError(Exception):
    """Raised when budget limit would be exceeded."""

    pass


@dataclass
class BudgetPolicy:
    """Budget constraints for an agent or operation.

    Attributes:
        name: Policy name
        total_budget_cents: Total budget in cents (None = unlimited)
        period_budget_cents: Budget per period in cents (None = unlimited)
        period: Budget reset period
        per_operation_limit_cents: Maximum per single operation in cents
        enabled: Whether this policy is active
    """

    name: str
    total_budget_cents: float | None = None
    period_budget_cents: float | None = None
    period: BudgetPeriod = BudgetPeriod.UNLIMITED
    per_operation_limit_cents: float | None = None
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate budget policy."""
        if not self.name:
            raise ValueError("name must be provided")
        if self.total_budget_cents is not None and self.total_budget_cents < 0:
            raise ValueError("total_budget_cents must be non-negative")
        if self.period_budget_cents is not None and self.period_budget_cents < 0:
            raise ValueError("period_budget_cents must be non-negative")
        if self.per_operation_limit_cents is not None and self.per_operation_limit_cents < 0:
            raise ValueError("per_operation_limit_cents must be non-negative")


@dataclass
class BudgetStatus:
    """Current budget status and consumption.

    Attributes:
        policy_name: Name of the budget policy
        total_spent_cents: Total spent to date
        period_spent_cents: Spent in current period
        remaining_total_cents: Remaining total budget
        remaining_period_cents: Remaining period budget
        can_spend: Whether more spending is allowed
        next_reset: When budget resets (if applicable)
    """

    policy_name: str
    total_spent_cents: float
    period_spent_cents: float
    remaining_total_cents: float | None
    remaining_period_cents: float | None
    can_spend: bool
    next_reset: datetime | None = None


class BudgetEnforcer:
    """Enforce budget constraints for LLM operations.

    This class tracks spending against defined budgets and prevents operations
    that would exceed limits.

    Usage:
        enforcer = BudgetEnforcer()

        # Set budget for agent
        enforcer.set_policy(
            BudgetPolicy(
                name="agent_openai",
                total_budget_cents=10000,  # $100 total
                period_budget_cents=2000,  # $20 per day
                period=BudgetPeriod.DAILY,
            )
        )

        # Check if operation would fit in budget
        try:
            enforcer.check_budget(
                policy_name="agent_openai",
                cost_cents=150,  # $1.50
            )
            # Operation is allowed
        except BudgetExceededError:
            # Operation would exceed budget
            pass
    """

    def __init__(self) -> None:
        """Initialize budget enforcer."""
        self._policies: dict[str, BudgetPolicy] = {}
        self._total_spent: dict[str, float] = {}
        self._period_spent: dict[str, float] = {}
        self._period_reset_time: dict[str, datetime] = {}

    def set_policy(self, policy: BudgetPolicy) -> None:
        """Set or update a budget policy.

        Args:
            policy: BudgetPolicy to set

        Raises:
            ValueError: If policy is invalid
        """
        if not policy:
            raise ValueError("policy must be provided")

        self._policies[policy.name] = policy
        if policy.name not in self._total_spent:
            self._total_spent[policy.name] = 0.0
        if policy.name not in self._period_spent:
            self._period_spent[policy.name] = 0.0
        if policy.name not in self._period_reset_time:
            self._period_reset_time[policy.name] = self._get_next_reset(policy.period)

    def check_budget(self, policy_name: str, cost_cents: float) -> bool:
        """Check if operation would fit within budget.

        Args:
            policy_name: Name of policy to check
            cost_cents: Cost of operation in cents

        Returns:
            True if operation is allowed

        Raises:
            BudgetExceededError: If operation would exceed budget
            ValueError: If policy not found
        """
        if not policy_name:
            raise ValueError("policy_name must be provided")
        if cost_cents < 0:
            raise ValueError("cost_cents must be non-negative")

        policy = self._policies.get(policy_name)
        if not policy:
            raise ValueError(f"No policy found: {policy_name}")

        if not policy.enabled:
            raise ValueError(f"Policy is not enabled: {policy_name}")

        # Check total budget
        if policy.total_budget_cents is not None:
            if self._total_spent[policy_name] + cost_cents > policy.total_budget_cents:
                raise BudgetExceededError(f"Operation would exceed total budget for {policy_name}")

        # Check period budget
        self._refresh_period_budget(policy_name)
        if policy.period_budget_cents is not None:
            if self._period_spent[policy_name] + cost_cents > policy.period_budget_cents:
                raise BudgetExceededError(f"Operation would exceed period budget for {policy_name}")

        # Check per-operation limit
        if policy.per_operation_limit_cents is not None:
            if cost_cents > policy.per_operation_limit_cents:
                raise BudgetExceededError(
                    f"Operation cost exceeds per-operation limit for {policy_name}"
                )

        return True

    def record_spending(self, policy_name: str, cost_cents: float) -> BudgetStatus:
        """Record spending against a budget.

        Should be called after an operation completes successfully.
        This assumes check_budget was called first.

        Args:
            policy_name: Name of policy
            cost_cents: Cost of operation in cents

        Returns:
            Updated BudgetStatus

        Raises:
            ValueError: If policy not found or cost is negative
        """
        if not policy_name:
            raise ValueError("policy_name must be provided")
        if cost_cents < 0:
            raise ValueError("cost_cents must be non-negative")

        if policy_name not in self._policies:
            raise ValueError(f"No policy found: {policy_name}")

        self._total_spent[policy_name] += cost_cents
        self._period_spent[policy_name] += cost_cents

        return self.get_status(policy_name)

    def get_status(self, policy_name: str) -> BudgetStatus:
        """Get current budget status.

        Args:
            policy_name: Name of policy

        Returns:
            BudgetStatus with current information

        Raises:
            ValueError: If policy not found
        """
        if policy_name not in self._policies:
            raise ValueError(f"No policy found: {policy_name}")

        policy = self._policies[policy_name]
        self._refresh_period_budget(policy_name)

        # Calculate remaining budgets
        remaining_total = None
        if policy.total_budget_cents is not None:
            remaining_total = policy.total_budget_cents - self._total_spent[policy_name]

        remaining_period = None
        if policy.period_budget_cents is not None:
            remaining_period = policy.period_budget_cents - self._period_spent[policy_name]

        # Determine if more spending is allowed
        can_spend = True
        if remaining_total is not None and remaining_total <= 0:
            can_spend = False
        if remaining_period is not None and remaining_period <= 0:
            can_spend = False

        return BudgetStatus(
            policy_name=policy_name,
            total_spent_cents=self._total_spent[policy_name],
            period_spent_cents=self._period_spent[policy_name],
            remaining_total_cents=remaining_total,
            remaining_period_cents=remaining_period,
            can_spend=can_spend,
            next_reset=self._period_reset_time.get(policy_name),
        )

    def reset_period(self, policy_name: str) -> BudgetStatus:
        """Manually reset period budget.

        Args:
            policy_name: Name of policy

        Returns:
            Updated BudgetStatus

        Raises:
            ValueError: If policy not found
        """
        if policy_name not in self._policies:
            raise ValueError(f"No policy found: {policy_name}")

        self._period_spent[policy_name] = 0.0
        policy = self._policies[policy_name]
        self._period_reset_time[policy_name] = self._get_next_reset(policy.period)

        return self.get_status(policy_name)

    def get_all_policies(self) -> dict[str, BudgetPolicy]:
        """Get all budget policies.

        Returns:
            Dict of policy names to BudgetPolicy objects
        """
        return dict(self._policies)

    def disable_policy(self, policy_name: str) -> bool:
        """Disable a policy (stops enforcement).

        Args:
            policy_name: Name of policy

        Returns:
            True if disabled, False if not found
        """
        policy = self._policies.get(policy_name)
        if not policy:
            return False

        policy.enabled = False
        return True

    def _refresh_period_budget(self, policy_name: str) -> None:
        """Refresh period budget if period has ended.

        Args:
            policy_name: Name of policy
        """
        policy = self._policies.get(policy_name)
        if not policy:
            return

        if policy.period == BudgetPeriod.UNLIMITED:
            return

        now = datetime.now()
        reset_time = self._period_reset_time.get(policy_name)

        if reset_time and now >= reset_time:
            self._period_spent[policy_name] = 0.0
            self._period_reset_time[policy_name] = self._get_next_reset(policy.period)

    def _get_next_reset(self, period: BudgetPeriod) -> datetime:
        """Calculate next budget reset time.

        Args:
            period: Budget period

        Returns:
            Datetime of next reset
        """
        now = datetime.now()

        if period == BudgetPeriod.DAILY:
            return now + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            return now + timedelta(weeks=1)
        elif period == BudgetPeriod.MONTHLY:
            return now + timedelta(days=30)
        else:
            return datetime.max
