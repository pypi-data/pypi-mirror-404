"""
Batch Optimizer for LLM API Call Optimization

This module provides batching and optimization strategies for LLM API calls
to maximize throughput and minimize costs.
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BatchStrategy(Enum):
    """Batching strategy for API calls."""

    IMMEDIATE = "immediate"  # No batching, send immediately
    TIME_WINDOW = "time_window"  # Wait for time window to fill batch
    SIZE_BASED = "size_based"  # Wait until batch size reached
    ADAPTIVE = "adaptive"  # Dynamically adjust based on traffic


@dataclass
class BatchRequest:
    """A single request in a batch."""

    request_id: str
    prompt: str
    model: str
    provider: str
    parameters: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # Higher priority processed first
    callback: Callable[..., Any] | None = None

    def __hash__(self) -> int:
        """Make request hashable for deduplication."""
        # Exclude request_id so identical prompts/models hash the same
        return hash((self.prompt, self.model, self.provider))


@dataclass
class BatchStats:
    """Statistics for batch optimization."""

    total_requests: int = 0
    batched_requests: int = 0
    immediate_requests: int = 0
    average_batch_size: float = 0.0
    batches_created: int = 0
    total_wait_time_ms: float = 0.0
    cost_savings_percent: float = 0.0


class BatchQueue:
    """Queue for managing batched requests."""

    def __init__(
        self, provider: str, model: str, max_batch_size: int = 10, max_wait_time_ms: float = 100.0
    ):
        self.provider = provider
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_wait_time_ms = max_wait_time_ms
        self.queue: list[BatchRequest] = []
        self.created_at = time.time()

    def add(self, request: BatchRequest) -> bool:
        """Add request to queue. Returns True if batch is ready."""
        self.queue.append(request)
        return self.is_ready()

    def is_ready(self) -> bool:
        """Check if batch is ready to be processed."""
        if not self.queue:
            return False

        # Size-based trigger
        if len(self.queue) >= self.max_batch_size:
            return True

        # Time-based trigger
        oldest_request = min(self.queue, key=lambda r: r.timestamp)
        wait_time_ms = (time.time() - oldest_request.timestamp) * 1000
        if wait_time_ms >= self.max_wait_time_ms:
            return True

        return False

    def get_batch(self) -> list[BatchRequest]:
        """Get and clear current batch."""
        batch = sorted(self.queue, key=lambda r: r.priority, reverse=True)
        self.queue = []
        return batch

    def size(self) -> int:
        """Get current queue size."""
        return len(self.queue)


class BatchOptimizer:
    """
    Optimizes LLM API calls through intelligent batching.

    Features:
    - Multiple batching strategies
    - Provider-specific batch limits
    - Priority-based request ordering
    - Cost optimization through batching
    - Real-time metrics tracking

    Example:
        optimizer = BatchOptimizer(strategy=BatchStrategy.ADAPTIVE)

        # Add requests
        request_id = optimizer.add_request(
            prompt="Hello world",
            model="gpt-4",
            provider="openai",
            parameters={"temperature": 0.7}
        )

        # Process batches
        batches = optimizer.get_ready_batches()
        for batch in batches:
            # Process batch...
            pass
    """

    # Provider-specific batch limits
    PROVIDER_LIMITS: dict[str, dict[str, int | float]] = {
        "openai": {"max_batch_size": 20, "max_wait_ms": 50},
        "anthropic": {"max_batch_size": 10, "max_wait_ms": 100},
        "google": {"max_batch_size": 15, "max_wait_ms": 75},
        "azure": {"max_batch_size": 20, "max_wait_ms": 50},
    }

    def __init__(
        self,
        strategy: BatchStrategy = BatchStrategy.ADAPTIVE,
        default_max_batch_size: int = 10,
        default_max_wait_ms: float = 100.0,
        enable_deduplication: bool = True,
    ):
        self.strategy = strategy
        self.default_max_batch_size = default_max_batch_size
        self.default_max_wait_ms = default_max_wait_ms
        self.enable_deduplication = enable_deduplication

        # Queues per provider/model combination
        self.queues: dict[tuple[str, str], BatchQueue] = {}

        # Request tracking
        self.pending_requests: dict[str, BatchRequest] = {}
        self.request_counter = 0

        # Statistics
        self.stats = BatchStats()

        # Deduplication tracking
        self.seen_requests: dict[int, list[str]] = defaultdict(list)

    def add_request(
        self,
        prompt: str,
        model: str,
        provider: str,
        parameters: dict[str, Any] | None = None,
        priority: int = 0,
        callback: Callable[..., Any] | None = None,
    ) -> str:
        """
        Add a request to the optimizer.

        Args:
            prompt: The prompt text
            model: Model name
            provider: Provider name
            parameters: Optional model parameters
            priority: Request priority (higher = processed first)
            callback: Optional callback when request completes

        Returns:
            Request ID for tracking
        """
        self.request_counter += 1
        request_id = f"req_{self.request_counter}_{int(time.time() * 1000)}"

        request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            model=model,
            provider=provider,
            parameters=parameters or {},
            priority=priority,
            callback=callback,
        )

        # Check for deduplication
        if self.enable_deduplication:
            request_hash = hash(request)
            if request_hash in self.seen_requests:
                # Duplicate request, add to tracking for result sharing
                self.seen_requests[request_hash].append(request_id)
                self.stats.total_requests += 1
                return request_id
            else:
                self.seen_requests[request_hash] = [request_id]

        # Handle IMMEDIATE strategy
        if self.strategy == BatchStrategy.IMMEDIATE:
            self.pending_requests[request_id] = request
            self.stats.total_requests += 1
            self.stats.immediate_requests += 1
            return request_id

        # Get or create queue for this provider/model
        queue_key = (provider, model)
        if queue_key not in self.queues:
            # Use provider-specific limits if available
            if provider in self.PROVIDER_LIMITS:
                limits = self.PROVIDER_LIMITS[provider]
            else:
                limits = {
                    "max_batch_size": self.default_max_batch_size,
                    "max_wait_ms": self.default_max_wait_ms,
                }

            self.queues[queue_key] = BatchQueue(
                provider=provider,
                model=model,
                max_batch_size=int(limits["max_batch_size"]),
                max_wait_time_ms=limits["max_wait_ms"],
            )

        # Add to queue
        self.queues[queue_key].add(request)
        self.pending_requests[request_id] = request
        self.stats.total_requests += 1

        return request_id

    def get_ready_batches(self) -> list[list[BatchRequest]]:
        """
        Get all batches that are ready to be processed.

        Returns:
            List of request batches
        """
        ready_batches = []

        # Handle immediate strategy
        if self.strategy == BatchStrategy.IMMEDIATE:
            for request in list(self.pending_requests.values()):
                ready_batches.append([request])
            return ready_batches

        # Check all queues for ready batches
        for _queue_key, queue in list(self.queues.items()):
            if queue.is_ready():
                batch = queue.get_batch()
                if batch:
                    ready_batches.append(batch)
                    self.stats.batches_created += 1
                    self.stats.batched_requests += len(batch)

                    # Update average batch size
                    if self.stats.batches_created > 0:
                        self.stats.average_batch_size = (
                            self.stats.batched_requests / self.stats.batches_created
                        )

                    # Calculate wait time
                    for request in batch:
                        wait_time_ms = (time.time() - request.timestamp) * 1000
                        self.stats.total_wait_time_ms += wait_time_ms

        return ready_batches

    def get_request(self, request_id: str) -> BatchRequest | None:
        """Get a pending request by ID."""
        return self.pending_requests.get(request_id)

    def remove_request(self, request_id: str) -> bool:
        """Remove a request from pending (after completion)."""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            return True
        return False

    def get_queue_status(self) -> dict[str, Any]:
        """Get status of all queues."""
        status = {}
        for (provider, model), queue in self.queues.items():
            key = f"{provider}/{model}"
            status[key] = {
                "size": queue.size(),
                "max_batch_size": queue.max_batch_size,
                "max_wait_ms": queue.max_wait_time_ms,
                "age_seconds": time.time() - queue.created_at,
                "is_ready": queue.is_ready(),
            }
        return status

    def get_stats(self) -> BatchStats:
        """Get optimization statistics."""
        # Calculate cost savings (batching reduces overhead)
        if self.stats.total_requests > 0:
            # Assume ~10% cost savings per batched request
            batching_ratio = self.stats.batched_requests / self.stats.total_requests
            self.stats.cost_savings_percent = batching_ratio * 10.0

        return self.stats

    def clear_queue(self, provider: str | None = None, model: str | None = None) -> None:
        """
        Clear queues matching criteria.

        Args:
            provider: Clear queues for this provider (None = all)
            model: Clear queues for this model (None = all)
        """
        if provider is None and model is None:
            # Clear all
            self.queues.clear()
            self.pending_requests.clear()
            return

        # Clear matching queues
        keys_to_remove = []
        for key in self.queues:
            queue_provider, queue_model = key
            if (provider is None or queue_provider == provider) and (
                model is None or queue_model == model
            ):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            # Remove pending requests in this queue
            queue = self.queues[key]
            for request in queue.queue:
                self.pending_requests.pop(request.request_id, None)
            del self.queues[key]

    def set_strategy(self, strategy: BatchStrategy) -> None:
        """Change batching strategy."""
        self.strategy = strategy

    def optimize_batch(self, batch: list[BatchRequest]) -> list[BatchRequest]:
        """
        Optimize a batch before processing.

        Applies optimizations like:
        - Deduplication
        - Reordering by priority
        - Grouping similar prompts

        Args:
            batch: Input batch

        Returns:
            Optimized batch
        """
        if not batch:
            return batch

        # Remove duplicates
        seen = set()
        deduplicated = []
        for request in batch:
            request_sig = (request.prompt, request.model, request.provider)
            if request_sig not in seen:
                seen.add(request_sig)
                deduplicated.append(request)

        # Sort by priority
        optimized = sorted(deduplicated, key=lambda r: r.priority, reverse=True)

        return optimized

    def get_pending_count(self) -> int:
        """Get total number of pending requests."""
        return len(self.pending_requests)

    def estimate_wait_time_ms(self, provider: str, model: str) -> float:
        """
        Estimate wait time for a new request.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            Estimated wait time in milliseconds
        """
        queue_key = (provider, model)
        if queue_key not in self.queues:
            return 0.0

        queue = self.queues[queue_key]
        if queue.is_ready():
            return 0.0

        # Estimate based on queue fill rate
        if queue.size() >= queue.max_batch_size * 0.8:
            return 10.0  # Almost full, will process soon
        else:
            return queue.max_wait_time_ms * 0.5  # Approximate average wait
