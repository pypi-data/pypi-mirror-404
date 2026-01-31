"""
Provider router for fallback chains and load balancing.

Inspired by LiteLLM's router, this module provides:
- Automatic failover between providers
- Round-robin load balancing
- Health checks and circuit breaker
- Rate limiting per provider

Example usage:
    # Fallback chain: primary → backup
    router = ProviderRouter(
        providers=["tavily", "serpapi", "google"],
        strategy="fallback",
    )
    result = router.execute(lambda p: p.search("AI news", 5, "en"))

    # Load balancing: distribute across providers
    router = ProviderRouter(
        providers=["tavily", "serpapi"],
        strategy="round-robin",
    )
    result = router.execute(lambda p: p.search("AI news", 5, "en"))
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import Any, Generic, TypeVar, cast

logger = logging.getLogger(__name__)

# Type variable for provider instances
T = TypeVar("T")


# ============================================================
# Router Strategies
# ============================================================


class RouterStrategy(str, Enum):
    """Routing strategies for provider selection."""

    FALLBACK = "fallback"  # Try providers in order until one succeeds
    ROUND_ROBIN = "round-robin"  # Distribute requests evenly across providers
    WEIGHTED = "weighted"  # Distribute based on weights
    LEAST_BUSY = "least-busy"  # Route to provider with fewest active requests


# ============================================================
# Circuit Breaker
# ============================================================


class CircuitBreaker:
    """
    Circuit breaker pattern for provider health tracking.

    Prevents cascading failures by temporarily disabling failing providers.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls to allow in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # State tracking per provider
        self._states: dict[str, str] = defaultdict(lambda: "closed")  # closed|open|half-open
        self._failure_counts: dict[str, int] = defaultdict(int)
        self._last_failure_time: dict[str, float] = {}
        self._half_open_calls: dict[str, int] = defaultdict(int)

    def call(self, provider_name: str, func: Callable[[], T]) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            provider_name: Provider identifier
            func: Function to execute

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from func
        """
        state = self._states[provider_name]

        # Check if circuit is open
        if state == "open":
            # Check if recovery timeout has passed
            last_failure = self._last_failure_time.get(provider_name, 0)
            if time.time() - last_failure >= self.recovery_timeout:
                # Transition to half-open
                logger.info(f"Circuit breaker for {provider_name}: open → half-open")
                self._states[provider_name] = "half-open"
                self._half_open_calls[provider_name] = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open for provider '{provider_name}'. "
                    f"Retry after {self.recovery_timeout - (time.time() - last_failure):.1f}s"
                )

        # Check half-open call limit
        if state == "half-open":
            if self._half_open_calls[provider_name] >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is half-open for provider '{provider_name}' "
                    f"and max calls ({self.half_open_max_calls}) reached"
                )
            self._half_open_calls[provider_name] += 1

        # Execute function
        try:
            result = func()

            # Success: reset failure count
            if self._failure_counts[provider_name] > 0:
                logger.info(f"Circuit breaker for {provider_name}: recovered after {self._failure_counts[provider_name]} failures")

            self._failure_counts[provider_name] = 0

            # Transition half-open → closed
            if state == "half-open":
                logger.info(f"Circuit breaker for {provider_name}: half-open → closed")
                self._states[provider_name] = "closed"

            return result

        except Exception:
            # Failure: increment count
            self._failure_counts[provider_name] += 1
            self._last_failure_time[provider_name] = time.time()

            # Check if threshold reached
            if self._failure_counts[provider_name] >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker for {provider_name}: closed → open "
                    f"(threshold: {self.failure_threshold})"
                )
                self._states[provider_name] = "open"

            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# ============================================================
# Rate Limiter
# ============================================================


class RateLimiter:
    """
    Token bucket rate limiter per provider.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per provider
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_second = requests_per_minute / 60.0

        # Token buckets per provider
        self._tokens: dict[str, float] = defaultdict(lambda: requests_per_minute)
        self._last_update: dict[str, float] = defaultdict(time.time)

    def acquire(self, provider_name: str) -> None:
        """
        Acquire a token (or wait if rate limit exceeded).

        Args:
            provider_name: Provider identifier

        Raises:
            RateLimitExceededError: If rate limit exceeded and no tokens available
        """
        now = time.time()

        # Refill tokens based on elapsed time
        elapsed = now - self._last_update[provider_name]
        self._tokens[provider_name] = min(
            self.requests_per_minute,
            self._tokens[provider_name] + elapsed * self.tokens_per_second,
        )
        self._last_update[provider_name] = now

        # Check if token available
        if self._tokens[provider_name] < 1.0:
            wait_time = (1.0 - self._tokens[provider_name]) / self.tokens_per_second
            raise RateLimitExceededError(
                f"Rate limit exceeded for provider '{provider_name}'. "
                f"Retry after {wait_time:.1f}s"
            )

        # Consume token
        self._tokens[provider_name] -= 1.0


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


# ============================================================
# Provider Router
# ============================================================


class ProviderRouter(Generic[T]):
    """
    Route requests across multiple providers with fallback and load balancing.

    Similar to LiteLLM's router for AI models, but generalized for any provider type.
    """

    def __init__(
        self,
        provider_getter: Callable[[str], T | ProviderRouter[T]],
        providers: list[str] | list[dict[str, Any]],
        strategy: RouterStrategy | str = RouterStrategy.FALLBACK,
        circuit_breaker_enabled: bool = True,
        rate_limit_per_minute: int | None = None,
    ):
        """
        Initialize provider router.

        Args:
            provider_getter: Function to get provider instance by name (e.g., get_search_provider)
                             Can return either a provider instance T or a ProviderRouter[T]
            providers: List of provider names or dicts with {name, weight}
            strategy: Routing strategy (fallback, round-robin, weighted, least-busy)
            circuit_breaker_enabled: Enable circuit breaker pattern
            rate_limit_per_minute: Optional rate limit per provider

        Example:
            router = ProviderRouter(
                provider_getter=get_search_provider,
                providers=["tavily", "serpapi", "google"],
                strategy="fallback",
            )
        """
        self.provider_getter = provider_getter
        self.strategy = RouterStrategy(strategy) if isinstance(strategy, str) else strategy

        # Parse provider configurations
        self.provider_configs: list[dict[str, Any]] = []
        for p in providers:
            if isinstance(p, str):
                self.provider_configs.append({"name": p, "weight": 1.0})
            else:
                self.provider_configs.append(p)

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker() if circuit_breaker_enabled else None

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(rate_limit_per_minute) if rate_limit_per_minute else None

        # Round-robin state
        self._round_robin_index = 0

        # Active request tracking for least-busy strategy
        self._active_requests: dict[str, int] = defaultdict(int)

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """
        Proxy method calls to underlying providers through execute().

        This makes ProviderRouter transparent - it acts like a provider itself.
        When you call router.search(...), it automatically routes through execute().

        Example:
            router = ProviderRouter(get_search_provider, ["tavily", "google"])
            # These two are equivalent:
            result = router.search("query", k=5, lang="en")
            result = router.execute(lambda p: p.search("query", k=5, lang="en"))
        """
        def method_proxy(*args: Any, **kwargs: Any) -> Any:
            return self.execute(lambda provider: getattr(provider, name)(*args, **kwargs))
        return method_proxy

    def execute(
        self,
        func: Callable[[T], Any],
        timeout: float | None = None,
    ) -> Any:
        """
        Execute a function with provider routing.

        Args:
            func: Function that takes a provider instance and returns a result
            timeout: Optional timeout in seconds (not yet implemented)

        Returns:
            Function result from first successful provider

        Raises:
            ProviderRoutingError: If all providers fail

        Example:
            result = router.execute(lambda p: p.search("AI news", 5, "en"))
        """
        if self.strategy == RouterStrategy.FALLBACK:
            return self._execute_fallback(func)
        elif self.strategy == RouterStrategy.ROUND_ROBIN:
            return self._execute_round_robin(func)
        elif self.strategy == RouterStrategy.WEIGHTED:
            return self._execute_weighted(func)
        elif self.strategy == RouterStrategy.LEAST_BUSY:
            return self._execute_least_busy(func)
        else:
            raise ValueError(f"Unknown routing strategy: {self.strategy}")

    def _execute_fallback(self, func: Callable[[T], Any]) -> Any:
        """Execute with fallback strategy: try providers in order."""
        errors = []

        for config in self.provider_configs:
            provider_name = config["name"]

            try:
                # Check rate limit
                if self.rate_limiter:
                    self.rate_limiter.acquire(provider_name)

                # Get provider instance
                provider = cast(T, self.provider_getter(provider_name))
                # Execute with circuit breaker
                if self.circuit_breaker:
                    result = self.circuit_breaker.call(provider_name, cast(Callable[[], Any], lambda p=provider: func(p)))
                else:
                    result = func(provider)

                logger.info(f"Provider router: succeeded with {provider_name}")
                return result

            except (CircuitBreakerOpenError, RateLimitExceededError) as e:
                # Skip this provider
                logger.warning(f"Provider router: skipping {provider_name}: {e}")
                errors.append(f"{provider_name}: {e}")
                continue

            except Exception as e:
                # Log and try next provider
                logger.warning(f"Provider router: {provider_name} failed: {e}")
                errors.append(f"{provider_name}: {e}")
                continue

        # All providers failed
        raise ProviderRoutingError(
            f"All providers failed. Errors: {'; '.join(errors)}"
        )

    def _execute_round_robin(self, func: Callable[[T], Any]) -> Any:
        """Execute with round-robin strategy: distribute load evenly."""
        # Try current provider in round-robin order
        for _ in range(len(self.provider_configs)):
            config = self.provider_configs[self._round_robin_index]
            provider_name = config["name"]

            # Advance round-robin index
            self._round_robin_index = (self._round_robin_index + 1) % len(self.provider_configs)

            try:
                # Check rate limit
                if self.rate_limiter:
                    self.rate_limiter.acquire(provider_name)

                # Get provider instance
                provider = cast(T, self.provider_getter(provider_name))
                # Execute with circuit breaker
                if self.circuit_breaker:
                    result = self.circuit_breaker.call(provider_name, cast(Callable[[], Any], lambda p=provider: func(p)))
                else:
                    result = func(provider)

                logger.info(f"Provider router (round-robin): succeeded with {provider_name}")
                return result

            except (CircuitBreakerOpenError, RateLimitExceededError):
                # Try next provider
                continue

            except Exception as e:
                logger.warning(f"Provider router (round-robin): {provider_name} failed: {e}")
                # Try next provider
                continue

        # All providers failed
        raise ProviderRoutingError("All providers failed (round-robin)")

    def _execute_weighted(self, func: Callable[[T], Any]) -> Any:
        """Execute with weighted strategy: not yet implemented."""
        # TODO: Implement weighted selection based on provider weights
        logger.warning("Weighted strategy not yet implemented, falling back to round-robin")
        return self._execute_round_robin(func)

    def _execute_least_busy(self, func: Callable[[T], Any]) -> Any:
        """Execute with least-busy strategy: route to provider with fewest active requests."""
        # Find least busy provider
        sorted_configs = sorted(
            self.provider_configs,
            key=lambda c: self._active_requests[c["name"]],
        )

        for config in sorted_configs:
            provider_name = config["name"]

            try:
                # Check rate limit
                if self.rate_limiter:
                    self.rate_limiter.acquire(provider_name)

                # Track active request
                self._active_requests[provider_name] += 1

                try:
                    # Get provider instance
                    provider = cast(T, self.provider_getter(provider_name))
                    # Execute with circuit breaker
                    if self.circuit_breaker:
                        result = self.circuit_breaker.call(provider_name, cast(Callable[[], Any], lambda p=provider: func(p)))
                    else:
                        result = func(provider)

                    logger.info(f"Provider router (least-busy): succeeded with {provider_name}")
                    return result

                finally:
                    # Decrement active request count
                    self._active_requests[provider_name] -= 1

            except (CircuitBreakerOpenError, RateLimitExceededError):
                # Try next provider
                continue

            except Exception as e:
                logger.warning(f"Provider router (least-busy): {provider_name} failed: {e}")
                # Try next provider
                continue

        # All providers failed
        raise ProviderRoutingError("All providers failed (least-busy)")


class ProviderRoutingError(Exception):
    """Raised when all providers in a router fail."""
    pass
