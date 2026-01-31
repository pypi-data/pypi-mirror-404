"""
Message Routing Skill

Thin wrapper around orchestrator.routing module for routing messages
and requests to appropriate handlers.
"""

from typing import Any, Optional

try:
    from orchestrator.routing import Route, Router  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    Route = None
    Router = None

# Global router instance
_router = None


def get_router() -> Router:
    """Get or create the global router instance."""
    global _router
    if _router is None:
        _router = Router()
    return _router


def route_message(
    message: str,
    message_type: str = "query",
    source: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Route a message to the appropriate handler."""
    router = get_router()

    route = router.route(
        message=message, message_type=message_type, source=source, context=context or {}
    )

    if route is None:
        return {"routed": False, "message": message, "handler": None}

    return {
        "routed": True,
        "message": message,
        "handler": route.handler,
        "route_id": route.id if hasattr(route, "id") else None,
    }


def get_routes(filter_type: str | None = None) -> list[dict[str, Any]]:
    """Get available routes."""
    router = get_router()

    routes = router.get_routes()
    if filter_type:
        routes = [r for r in routes if r.message_type == filter_type]

    return [
        {
            "id": r.id if hasattr(r, "id") else str(r),
            "handler": r.handler if hasattr(r, "handler") else None,
            "pattern": str(r),
        }
        for r in routes
    ]


def register_route(
    pattern: str, handler: str, priority: int = 0, conditions: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Register a new message route."""
    router = get_router()

    route = Route(pattern=pattern, handler=handler, priority=priority, conditions=conditions or {})

    router.register_route(route)

    return {"registered": True, "pattern": pattern, "handler": handler, "priority": priority}


def evaluate_route(route_id: str, message: str) -> bool:
    """Evaluate if a message matches a route."""
    router = get_router()

    routes = router.get_routes()
    for route in routes:
        route_str_id = route.id if hasattr(route, "id") else str(route)
        if route_str_id == route_id:
            # Check if message matches route
            if hasattr(route, "matches"):
                result = route.matches(message)
                # Ensure boolean result
                return bool(result)
            return True

    return False


def get_routing_stats() -> dict[str, Any]:
    """Get message routing statistics."""
    router = get_router()

    stats = {
        "total_routes": len(router.get_routes()),
        "routed_messages": getattr(router, "routed_count", 0),
        "unrouted_messages": getattr(router, "unrouted_count", 0),
    }

    return stats


__all__ = ["route_message", "get_routes", "register_route", "evaluate_route", "get_routing_stats"]
