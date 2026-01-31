"""Cost ledger for transaction recording and tracking.

This module provides transaction recording and cost tracking, enabling
detailed cost analysis and reporting.

Transaction Types:
  - API call: Cost from LLM API call
  - Cache hit: Cost savings from cache hit
  - Batch operation: Cost from batched operations
  - Refund: Manual refund/adjustment

Architecture:
  - Transaction: Individual transaction record
  - CostLedger: Transaction ledger and reporting
  - Query: Support for transaction queries and filtering
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TransactionType(Enum):
    """Type of cost transaction."""

    API_CALL = "api_call"
    CACHE_HIT = "cache_hit"
    BATCH_OPERATION = "batch_operation"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


@dataclass
class Transaction:
    """Individual cost transaction.

    Attributes:
        transaction_id: Unique transaction identifier
        timestamp: When transaction occurred
        type: Type of transaction
        policy_name: Budget policy name (agent/operation identifier)
        model: Model used (for API calls)
        prompt_tokens: Input tokens (for API calls)
        completion_tokens: Output tokens (for API calls)
        cost_cents: Cost in cents (negative for savings)
        description: Human-readable description
        metadata: Additional metadata
    """

    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    type: TransactionType = TransactionType.API_CALL
    policy_name: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_cents: float = 0.0
    description: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate transaction."""
        if not self.transaction_id:
            raise ValueError("transaction_id must be provided")
        if not self.policy_name:
            raise ValueError("policy_name must be provided")
        if self.type == TransactionType.API_CALL and not self.model:
            raise ValueError("model must be provided for API_CALL transactions")


@dataclass
class AggregatedCost:
    """Aggregated cost information.

    Attributes:
        total_cost_cents: Total cost
        transaction_count: Number of transactions
        average_cost_cents: Average cost per transaction
        model_breakdown: Costs by model
        type_breakdown: Costs by transaction type
    """

    total_cost_cents: float
    transaction_count: int
    average_cost_cents: float
    model_breakdown: dict[str, float] = field(default_factory=dict)
    type_breakdown: dict[str, float] = field(default_factory=dict)


class CostLedger:
    """Record and query LLM costs.

    This class maintains a ledger of all cost transactions and provides
    querying and reporting capabilities.

    Usage:
        ledger = CostLedger()

        # Record API call cost
        transaction = ledger.record_transaction(
            Transaction(
                policy_name="agent_openai",
                type=TransactionType.API_CALL,
                model="gpt-4",
                prompt_tokens=100,
                completion_tokens=50,
                cost_cents=150,
                description="Question answering",
            )
        )

        # Query transactions
        transactions = ledger.get_transactions(policy_name="agent_openai")

        # Get cost summary
        summary = ledger.get_cost_summary(policy_name="agent_openai")
    """

    def __init__(self) -> None:
        """Initialize cost ledger."""
        self._transactions: list[Transaction] = []
        self._index_by_policy: dict[str, list[Transaction]] = {}
        self._index_by_model: dict[str, list[Transaction]] = {}

    def record_transaction(self, transaction: Transaction) -> Transaction:
        """Record a transaction in the ledger.

        Args:
            transaction: Transaction to record

        Returns:
            Recorded transaction (may have timestamp/ID set)

        Raises:
            ValueError: If transaction is invalid
        """
        if not transaction:
            raise ValueError("transaction must be provided")

        # Validate transaction
        try:
            # Post-init validation will run
            pass
        except ValueError as e:
            raise ValueError(f"Invalid transaction: {e}") from None

        self._transactions.append(transaction)

        # Update indices
        if transaction.policy_name not in self._index_by_policy:
            self._index_by_policy[transaction.policy_name] = []
        self._index_by_policy[transaction.policy_name].append(transaction)

        if transaction.model and transaction.model not in self._index_by_model:
            self._index_by_model[transaction.model] = []
        if transaction.model:
            self._index_by_model[transaction.model].append(transaction)

        return transaction

    def get_transactions(
        self,
        policy_name: str | None = None,
        model: str | None = None,
        transaction_type: TransactionType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        """Query transactions from the ledger.

        Args:
            policy_name: Filter by policy name
            model: Filter by model
            transaction_type: Filter by transaction type
            start_time: Include only transactions after this time
            end_time: Include only transactions before this time
            limit: Maximum number of transactions to return

        Returns:
            List of matching transactions
        """
        # Start with all transactions or policy subset
        if policy_name:
            results = self._index_by_policy.get(policy_name, [])
        else:
            results = list(self._transactions)

        # Apply filters
        if model:
            results = [t for t in results if t.model == model]

        if transaction_type:
            results = [t for t in results if t.type == transaction_type]

        if start_time:
            results = [t for t in results if t.timestamp >= start_time]

        if end_time:
            results = [t for t in results if t.timestamp <= end_time]

        # Apply limit
        if limit and limit > 0:
            results = results[-limit:]

        return results

    def get_cost_summary(
        self,
        policy_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> AggregatedCost:
        """Get aggregated cost summary.

        Args:
            policy_name: Filter by policy name
            start_time: Include only transactions after this time
            end_time: Include only transactions before this time

        Returns:
            AggregatedCost with summary information
        """
        transactions = self.get_transactions(
            policy_name=policy_name,
            start_time=start_time,
            end_time=end_time,
        )

        if not transactions:
            return AggregatedCost(
                total_cost_cents=0.0,
                transaction_count=0,
                average_cost_cents=0.0,
                model_breakdown={},
                type_breakdown={},
            )

        # Calculate totals
        total_cost = sum(t.cost_cents for t in transactions)
        count = len(transactions)
        average_cost = total_cost / count if count > 0 else 0.0

        # Calculate model breakdown
        model_breakdown: dict[str, float] = {}
        for transaction in transactions:
            if transaction.model:
                if transaction.model not in model_breakdown:
                    model_breakdown[transaction.model] = 0.0
                model_breakdown[transaction.model] += transaction.cost_cents

        # Calculate type breakdown
        type_breakdown: dict[str, float] = {}
        for transaction in transactions:
            type_name = transaction.type.value
            if type_name not in type_breakdown:
                type_breakdown[type_name] = 0.0
            type_breakdown[type_name] += transaction.cost_cents

        return AggregatedCost(
            total_cost_cents=total_cost,
            transaction_count=count,
            average_cost_cents=average_cost,
            model_breakdown=model_breakdown,
            type_breakdown=type_breakdown,
        )

    def get_all_policies(self) -> list[str]:
        """Get list of all policies with transactions.

        Returns:
            List of unique policy names
        """
        return list(self._index_by_policy.keys())

    def get_all_models(self) -> list[str]:
        """Get list of all models with transactions.

        Returns:
            List of unique model names
        """
        return list(self._index_by_model.keys())

    def export_transactions(self, policy_name: str | None = None) -> list[dict[str, Any]]:
        """Export transactions as dictionaries for serialization.

        Args:
            policy_name: Filter by policy name

        Returns:
            List of transaction dictionaries
        """
        transactions = self.get_transactions(policy_name=policy_name)

        return [
            {
                "transaction_id": t.transaction_id,
                "timestamp": t.timestamp.isoformat(),
                "type": t.type.value,
                "policy_name": t.policy_name,
                "model": t.model,
                "prompt_tokens": t.prompt_tokens,
                "completion_tokens": t.completion_tokens,
                "cost_cents": t.cost_cents,
                "description": t.description,
                "metadata": t.metadata,
            }
            for t in transactions
        ]

    def clear_transactions(self, policy_name: str | None = None) -> int:
        """Clear transactions from ledger.

        Args:
            policy_name: Only clear for this policy (None = clear all)

        Returns:
            Number of transactions cleared
        """
        if policy_name:
            count = len(self._index_by_policy.get(policy_name, []))
            self._transactions = [t for t in self._transactions if t.policy_name != policy_name]
            if policy_name in self._index_by_policy:
                del self._index_by_policy[policy_name]
            return count
        else:
            count = len(self._transactions)
            self._transactions.clear()
            self._index_by_policy.clear()
            self._index_by_model.clear()
            return count

    def get_transaction_count(self) -> int:
        """Get total number of transactions in ledger.

        Returns:
            Number of transactions
        """
        return len(self._transactions)
