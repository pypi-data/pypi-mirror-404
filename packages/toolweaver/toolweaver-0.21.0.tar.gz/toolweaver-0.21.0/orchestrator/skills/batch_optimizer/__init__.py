"""
Batch Optimizer Skill

Thin wrapper around orchestrator._internal.cost.batch_optimizer
following the Agent Skills specification.
"""

from typing import Any, Optional

from orchestrator._internal.cost.batch_optimizer import BatchOptimizer, BatchRequest, BatchStrategy


class Skill:
    """
    Batch Optimizer Skill following Agent Skills specification.

    Thin wrapper around orchestrator._internal.cost.batch_optimizer.
    Optimizes batching of API requests to reduce cost.
    """

    def __init__(self) -> None:
        """Initialize batch optimizer skill."""
        self._optimizer = BatchOptimizer(strategy=BatchStrategy.ADAPTIVE)

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Main skill execution method."""
        return {"success": True, "message": "Batch optimizer ready"}


# Global optimizer instance
_optimizer = None


def get_optimizer() -> BatchOptimizer:
    """Get or create the global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = BatchOptimizer(strategy=BatchStrategy.ADAPTIVE)
    return _optimizer


def add_request(
    request_id: str,
    prompt: str,
    model: str,
    provider: str,
    priority: int = 0,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add a request to the batch queue."""
    optimizer = get_optimizer()

    actual_request_id = optimizer.add_request(
        prompt=prompt,
        model=model,
        provider=provider,
        parameters=parameters or {},
        priority=priority,
    )

    return {
        "request_id": actual_request_id,
        "prompt": prompt,
        "model": model,
        "provider": provider,
        "priority": priority,
    }


def get_batches(force: bool = False) -> list[dict[str, Any]]:
    """Get optimized batches ready for processing."""
    optimizer = get_optimizer()
    batches = optimizer.get_ready_batches()

    return [
        {
            "batch_id": f"batch_{i}",
            "size": len(batch),
            "provider": batch[0].provider if batch else None,
            "requests": [
                {
                    "request_id": req.request_id,
                    "prompt": req.prompt[:100],  # Truncate for display
                    "model": req.model,
                    "priority": req.priority,
                }
                for req in batch
            ],
        }
        for i, batch in enumerate(batches)
    ]


def optimize_batch(batch_id: str, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Optimize a specific batch by removing duplicates and reordering."""
    optimizer = get_optimizer()

    # Convert dicts to BatchRequest objects
    queue_requests = [
        BatchRequest(
            request_id=req["request_id"],
            prompt=req["prompt"],
            model=req["model"],
            provider=req["provider"],
            priority=req.get("priority", 0),
            parameters=req.get("parameters", {}),
        )
        for req in requests
    ]

    optimized = optimizer.deduplicate_batch(queue_requests)  # type: ignore[attr-defined]

    return [
        {
            "request_id": req.request_id,
            "prompt": req.prompt,
            "model": req.model,
            "provider": req.provider,
            "priority": req.priority,
        }
        for req in optimized
    ]


def set_strategy(strategy: str) -> str:
    """Set the batching strategy."""
    optimizer = get_optimizer()

    strategy_map = {
        "IMMEDIATE": BatchStrategy.IMMEDIATE,
        "SIZE_BASED": BatchStrategy.SIZE_BASED,
        "TIME_WINDOW": BatchStrategy.TIME_WINDOW,
        "ADAPTIVE": BatchStrategy.ADAPTIVE,
    }

    if strategy not in strategy_map:
        valid = ", ".join(strategy_map.keys())
        return f"Invalid strategy. Valid options: {valid}"

    optimizer.set_strategy(strategy_map[strategy])
    return f"Strategy set to {strategy}"


def get_stats() -> dict[str, Any]:
    """Get batch optimizer statistics."""
    optimizer = get_optimizer()
    stats = optimizer.get_stats()
    # Convert BatchStats dataclass to dict
    return stats.__dict__ if hasattr(stats, "__dict__") else stats  # type: ignore[return-value]


def clear_queue() -> int:
    """Clear all pending requests."""
    optimizer = get_optimizer()
    count = sum(len(queue.queue) for queue in optimizer.queues.values())
    optimizer.queues.clear()
    return count


__all__ = [
    "add_request",
    "get_batches",
    "optimize_batch",
    "set_strategy",
    "get_stats",
    "clear_queue",
]
