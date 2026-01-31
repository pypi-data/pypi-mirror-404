"""Message routing integration for automatic cost tracking.

This module integrates cost tracking with the orchestrator's message routing
system, enabling automatic tracking of all API calls through the router.

Architecture:
  - CostTrackingMiddleware: Middleware for automatic tracking
  - MessageRouterIntegration: Router integration layer
  - CostInterceptor: Intercepts and tracks costs
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class CostTrackingMiddleware:
    """Middleware for automatic cost tracking in message routing.

    Intercepts messages in the routing pipeline to track costs automatically.
    """

    def __init__(self, cost_controller: Any) -> None:
        """Initialize middleware.

        Args:
            cost_controller: CostController instance
        """
        self.cost_controller = cost_controller
        self.enabled = True
        self._call_count = 0
        self._tracked_cost = 0.0

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable tracking.

        Args:
            enabled: Whether to enable tracking
        """
        self.enabled = enabled

    def is_enabled(self) -> bool:
        """Check if middleware is enabled.

        Returns:
            True if enabled
        """
        return self.enabled

    def should_track(self, message: dict[str, Any]) -> bool:
        """Determine if message should be tracked.

        Args:
            message: Message dictionary

        Returns:
            True if should track
        """
        if not self.enabled:
            return False

        # Don't track messages without model info
        if "model" not in message:
            return False

        # Don't track if cost tracking is globally disabled
        if not self.cost_controller.is_tracking_enabled():
            return False

        return True

    def extract_cost_info(self, message: dict[str, Any]) -> dict[str, Any]:
        """Extract cost-relevant information from message.

        Args:
            message: Message dictionary

        Returns:
            Dictionary with cost info
        """
        return {
            "model": message.get("model"),
            "agent_name": message.get("agent_name", message.get("from")),
            "prompt_tokens": message.get("prompt_tokens", 0),
            "completion_tokens": message.get("completion_tokens", 0),
            "source": message.get("type", "unknown"),
            "timestamp": datetime.now(),
        }

    def process_request(
        self, message: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Process outgoing message.

        Args:
            message: Message to process

        Returns:
            Tuple of (processed_message, cost_info)
        """
        if not self.should_track(message):
            return message, None

        cost_info = self.extract_cost_info(message)

        # Augment message with tracking info
        message["_tracked"] = True
        message["_track_start"] = datetime.now()

        return message, cost_info

    def process_response(
        self, message: dict[str, Any], response: Any, cost_info: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, Any] | None]:
        """Process incoming response.

        Args:
            message: Original message
            response: Response from API
            cost_info: Cost info extracted from request

        Returns:
            Tuple of (response, cost_tracking_result)
        """
        if not cost_info:
            return response, None

        try:
            # Extract actual token usage from response
            if isinstance(response, dict):
                prompt_tokens = response.get("prompt_tokens", cost_info.get("prompt_tokens", 0))
                completion_tokens = response.get(
                    "completion_tokens", cost_info.get("completion_tokens", 0)
                )
            else:
                prompt_tokens = cost_info.get("prompt_tokens", 0)
                completion_tokens = cost_info.get("completion_tokens", 0)

            # Track the call
            result = self.cost_controller.track_api_call(
                agent_name=cost_info.get("agent_name"),
                model=cost_info.get("model"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            self._call_count += 1
            if isinstance(result, dict):
                self._tracked_cost += result.get("total_cost_cents", 0)

            return response, {
                "tracked": True,
                "cost_info": result,
            }
        except Exception as e:
            logger.warning(f"Failed to track cost for message: {e}")
            return response, {
                "tracked": False,
                "error": str(e),
            }

    def get_stats(self) -> dict[str, Any]:
        """Get middleware statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "enabled": self.enabled,
            "calls_tracked": self._call_count,
            "total_cost_cents": self._tracked_cost,
            "average_cost_per_call": self._tracked_cost / self._call_count
            if self._call_count > 0
            else 0,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._call_count = 0
        self._tracked_cost = 0.0


class MessageRouterIntegration:
    """Integration layer between cost tracking and message router.

    Provides methods to register and manage cost tracking in the message router.
    """

    def __init__(self, cost_controller: Any, message_router: Any = None) -> None:
        """Initialize integration.

        Args:
            cost_controller: CostController instance
            message_router: MessageRouter instance (optional)
        """
        self.cost_controller = cost_controller
        self.message_router = message_router
        self.middleware = CostTrackingMiddleware(cost_controller)
        self._is_registered = False
        self._routing_costs: dict[str, float] = {}

    def register_cost_tracking(self) -> bool:
        """Register cost tracking middleware with router.

        Returns:
            True if successfully registered
        """
        if not self.message_router:
            logger.warning("No message router provided, skipping registration")
            return False

        try:
            # In a real implementation, this would register the middleware
            # with the message router's pipeline
            self._is_registered = True
            logger.info("Cost tracking middleware registered with message router")
            return True
        except Exception as e:
            logger.error(f"Failed to register cost tracking: {e}")
            return False

    def unregister_cost_tracking(self) -> bool:
        """Unregister cost tracking middleware.

        Returns:
            True if successfully unregistered
        """
        if not self._is_registered:
            return False

        try:
            self._is_registered = False
            logger.info("Cost tracking middleware unregistered from message router")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister cost tracking: {e}")
            return False

    def is_registered(self) -> bool:
        """Check if cost tracking is registered.

        Returns:
            True if registered
        """
        return self._is_registered

    def route_with_cost_tracking(
        self, message: dict[str, Any], agent_name: str
    ) -> tuple[Any, dict[str, Any]]:
        """Route a message with cost tracking.

        Args:
            message: Message to route
            agent_name: Name of agent

        Returns:
            Tuple of (response, cost_info)
        """
        # Add agent name to message
        message["agent_name"] = agent_name

        # Process request
        processed_message, cost_info = self.middleware.process_request(message)

        # Route message (if router available)
        if self.message_router:
            try:
                response = self.message_router.route(processed_message)
            except Exception as e:
                logger.error(f"Error routing message: {e}")
                response = None
        else:
            response = None

        # Process response
        final_response, tracking_result = self.middleware.process_response(
            processed_message, response, cost_info
        )

        # Track in our records
        if agent_name and tracking_result and tracking_result.get("tracked"):
            self._routing_costs[agent_name] = self._routing_costs.get(
                agent_name, 0
            ) + tracking_result.get("cost_info", {}).get("total_cost_cents", 0)

        return final_response, {
            "response": final_response,
            "cost_info": tracking_result,
            "agent_name": agent_name,
        }

    def get_routing_costs(self, agent_name: str | None = None) -> dict[str, float]:
        """Get accumulated costs from routing.

        Args:
            agent_name: Filter by agent (None = all)

        Returns:
            Dictionary of costs
        """
        if agent_name:
            return {agent_name: self._routing_costs.get(agent_name, 0.0)}
        return self._routing_costs.copy()

    def reset_routing_costs(self) -> None:
        """Reset routing cost tracking."""
        self._routing_costs.clear()

    def get_integration_stats(self) -> dict[str, Any]:
        """Get integration statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "is_registered": self._is_registered,
            "middleware_enabled": self.middleware.is_enabled(),
            "middleware_stats": self.middleware.get_stats(),
            "routing_costs": self._routing_costs,
            "total_routing_cost": sum(self._routing_costs.values()),
        }


class AgentCostRegistry:
    """Registry for agent cost policies and constraints.

    Maintains per-agent cost configuration including budgets and preferences.
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._agent_profiles: dict[str, dict[str, Any]] = {}

    def register_agent_cost_profile(
        self,
        agent_name: str,
        budget_cents: float | None = None,
        cost_tracking_enabled: bool = True,
        cost_alerts_enabled: bool = True,
        preferred_models: list[str] | None = None,
    ) -> bool:
        """Register or update agent cost profile.

        Args:
            agent_name: Name of agent
            budget_cents: Budget limit in cents
            cost_tracking_enabled: Whether to track costs
            cost_alerts_enabled: Whether to send alerts
            preferred_models: Preferred models to use

        Returns:
            True if successfully registered
        """
        try:
            self._agent_profiles[agent_name] = {
                "agent_name": agent_name,
                "budget_cents": budget_cents,
                "cost_tracking_enabled": cost_tracking_enabled,
                "cost_alerts_enabled": cost_alerts_enabled,
                "preferred_models": preferred_models or [],
                "registered_at": datetime.now(),
            }
            return True
        except Exception as e:
            logger.error(f"Failed to register agent profile: {e}")
            return False

    def get_agent_cost_profile(self, agent_name: str) -> dict[str, Any] | None:
        """Get agent cost profile.

        Args:
            agent_name: Name of agent

        Returns:
            Profile dictionary or None if not found
        """
        return self._agent_profiles.get(agent_name)

    def update_agent_budget(self, agent_name: str, budget_cents: float) -> bool:
        """Update agent budget.

        Args:
            agent_name: Name of agent
            budget_cents: New budget in cents

        Returns:
            True if successfully updated
        """
        if agent_name not in self._agent_profiles:
            return False

        try:
            self._agent_profiles[agent_name]["budget_cents"] = budget_cents
            return True
        except Exception as e:
            logger.error(f"Failed to update agent budget: {e}")
            return False

    def set_tracking_enabled(self, agent_name: str, enabled: bool) -> bool:
        """Enable or disable tracking for agent.

        Args:
            agent_name: Name of agent
            enabled: Whether to enable tracking

        Returns:
            True if successful
        """
        if agent_name not in self._agent_profiles:
            return False

        try:
            self._agent_profiles[agent_name]["cost_tracking_enabled"] = enabled
            return True
        except Exception as e:
            logger.error(f"Failed to update tracking setting: {e}")
            return False

    def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """Get all agent profiles.

        Returns:
            Dictionary of all profiles
        """
        return self._agent_profiles.copy()

    def remove_agent_profile(self, agent_name: str) -> bool:
        """Remove agent profile.

        Args:
            agent_name: Name of agent

        Returns:
            True if successfully removed
        """
        if agent_name in self._agent_profiles:
            del self._agent_profiles[agent_name]
            return True
        return False

    def get_agents_by_status(self, tracking_enabled: bool | None = None) -> list[str]:
        """Get agents filtered by status.

        Args:
            tracking_enabled: Filter by tracking status

        Returns:
            List of agent names
        """
        agents = []
        for agent_name, profile in self._agent_profiles.items():
            if tracking_enabled is None:
                agents.append(agent_name)
            elif profile.get("cost_tracking_enabled") == tracking_enabled:
                agents.append(agent_name)
        return agents
