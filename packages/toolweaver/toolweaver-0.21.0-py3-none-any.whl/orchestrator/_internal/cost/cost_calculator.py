"""Cost calculation from token counts.

This module provides cost calculation for LLM API calls based on token counts
and model pricing information.

Pricing Strategy:
  - Per-provider pricing models
  - Separate input/output token pricing
  - Support for model-specific pricing tiers
  - Caching for pricing lookups

Architecture:
  - PricingModel: Defines pricing for a model
  - CostCalculator: Calculates costs from token counts
  - Integration with TokenCounter for complete cost tracking
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Currency(Enum):
    """Supported currencies for cost calculation."""

    USD = "usd"
    EUR = "eur"
    GBP = "gbp"


@dataclass
class PricingModel:
    """Pricing information for an LLM model.

    Attributes:
        model: Model identifier
        provider: LLM provider name
        input_price_per_1k: Price per 1000 input tokens (in cents)
        output_price_per_1k: Price per 1000 output tokens (in cents)
        currency: Currency for pricing
        active: Whether this pricing is currently active
    """

    model: str
    provider: str
    input_price_per_1k: float
    output_price_per_1k: float
    currency: Currency = Currency.USD
    active: bool = True

    def __post_init__(self) -> None:
        """Validate pricing model."""
        if self.input_price_per_1k < 0:
            raise ValueError("input_price_per_1k must be non-negative")
        if self.output_price_per_1k < 0:
            raise ValueError("output_price_per_1k must be non-negative")
        if not self.model:
            raise ValueError("model must be provided")
        if not self.provider:
            raise ValueError("provider must be provided")


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for an API call.

    Attributes:
        model: Model used
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        input_cost: Cost of input tokens (in cents)
        output_cost: Cost of output tokens (in cents)
        total_cost: Total cost (in cents)
        currency: Currency for costs
    """

    model: str
    prompt_tokens: int
    completion_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    currency: Currency = Currency.USD

    def __post_init__(self) -> None:
        """Validate cost breakdown."""
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.input_cost < 0:
            raise ValueError("input_cost must be non-negative")
        if self.output_cost < 0:
            raise ValueError("output_cost must be non-negative")
        if abs(self.total_cost - (self.input_cost + self.output_cost)) > 0.001:
            raise ValueError("total_cost must equal input_cost + output_cost")


class CostCalculator:
    """Calculate costs for LLM API calls.

    This class maintains pricing models for various LLM providers and calculates
    costs based on token counts.

    Usage:
        calculator = CostCalculator()

        # Register pricing
        calculator.register_pricing(
            PricingModel(
                model="gpt-4",
                provider="openai",
                input_price_per_1k=3.0,  # $0.03 per 1K input tokens
                output_price_per_1k=6.0,  # $0.06 per 1K output tokens
            )
        )

        # Calculate cost
        breakdown = calculator.calculate_cost(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )
    """

    # Default pricing for common models (in cents per 1K tokens)
    _DEFAULT_PRICING = {
        "gpt-3.5-turbo": {
            "provider": "openai",
            "input": 0.0005,
            "output": 0.0015,
        },
        "gpt-4": {
            "provider": "openai",
            "input": 0.03,
            "output": 0.06,
        },
        "gpt-4-turbo": {
            "provider": "openai",
            "input": 0.01,
            "output": 0.03,
        },
        "gpt-4o": {
            "provider": "openai",
            "input": 0.005,
            "output": 0.015,
        },
        "claude-3-opus-20240229": {
            "provider": "anthropic",
            "input": 0.015,
            "output": 0.075,
        },
        "claude-3-sonnet-20240229": {
            "provider": "anthropic",
            "input": 0.003,
            "output": 0.015,
        },
        "claude-3-haiku-20240307": {
            "provider": "anthropic",
            "input": 0.00025,
            "output": 0.00125,
        },
    }

    def __init__(self) -> None:
        """Initialize cost calculator with default pricing."""
        self._pricing: dict[str, PricingModel] = {}
        self._load_default_pricing()

    def _load_default_pricing(self) -> None:
        """Load default pricing models."""
        for model_name, pricing_info in self._DEFAULT_PRICING.items():
            try:
                self.register_pricing(
                    PricingModel(
                        model=model_name,
                        provider=str(pricing_info["provider"]),
                        input_price_per_1k=float(str(pricing_info["input"])),
                        output_price_per_1k=float(str(pricing_info["output"])),
                    )
                )
            except ValueError:
                # Skip invalid pricing entries
                pass

    def register_pricing(self, pricing: PricingModel) -> None:
        """Register or update pricing for a model.

        Args:
            pricing: PricingModel with pricing information

        Raises:
            ValueError: If pricing model is invalid
        """
        if not pricing:
            raise ValueError("pricing must be provided")

        self._pricing[pricing.model] = pricing

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int = 0,
        currency: Currency = Currency.USD,
    ) -> CostBreakdown:
        """Calculate cost for API call.

        Args:
            model: Model identifier
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens (default: 0)
            currency: Currency for cost (default: USD)

        Returns:
            CostBreakdown with detailed cost information

        Raises:
            ValueError: If model not found or invalid tokens
        """
        if not model:
            raise ValueError("model must be provided")
        if prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")

        pricing = self._pricing.get(model)
        if not pricing:
            raise ValueError(f"No pricing found for model: {model}")

        if not pricing.active:
            raise ValueError(f"Pricing for model {model} is not active")

        # Calculate costs in cents
        input_cost = (prompt_tokens / 1000.0) * pricing.input_price_per_1k
        output_cost = (completion_tokens / 1000.0) * pricing.output_price_per_1k
        total_cost = input_cost + output_cost

        return CostBreakdown(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            currency=currency,
        )

    def get_pricing(self, model: str) -> PricingModel | None:
        """Get pricing information for a model.

        Args:
            model: Model identifier

        Returns:
            PricingModel if found, None otherwise
        """
        return self._pricing.get(model)

    def list_models(self) -> dict[str, PricingModel]:
        """List all available pricing models.

        Returns:
            Dict of model names to PricingModel objects
        """
        return {name: pricing for name, pricing in self._pricing.items() if pricing.active}

    def update_pricing(self, model: str, **kwargs: Any) -> PricingModel | None:
        """Update pricing for an existing model.

        Args:
            model: Model identifier
            **kwargs: Fields to update (input_price_per_1k, output_price_per_1k, active)

        Returns:
            Updated PricingModel or None if not found

        Raises:
            ValueError: If update is invalid
        """
        pricing = self._pricing.get(model)
        if not pricing:
            return None

        # Create updated pricing model
        updated_fields = {
            "model": pricing.model,
            "provider": pricing.provider,
            "input_price_per_1k": kwargs.get("input_price_per_1k", pricing.input_price_per_1k),
            "output_price_per_1k": kwargs.get("output_price_per_1k", pricing.output_price_per_1k),
            "currency": kwargs.get("currency", pricing.currency),
            "active": kwargs.get("active", pricing.active),
        }

        updated_pricing = PricingModel(**updated_fields)
        self._pricing[model] = updated_pricing
        return updated_pricing

    def deactivate_pricing(self, model: str) -> bool:
        """Deactivate pricing for a model (but keep it in registry).

        Args:
            model: Model identifier

        Returns:
            True if deactivated, False if not found
        """
        pricing = self._pricing.get(model)
        if not pricing:
            return False

        updated = self.update_pricing(model, active=False)
        return updated is not None

    def clear_pricing(self) -> None:
        """Clear all pricing models."""
        self._pricing.clear()
