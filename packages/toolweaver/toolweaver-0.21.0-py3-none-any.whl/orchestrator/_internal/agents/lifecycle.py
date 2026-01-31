"""
Agent Lifecycle Management

Provides centralized lifecycle management for agents including initialization,
registration, health monitoring, and graceful shutdown.

Components:
- AgentLifecycleManager: Manages agent lifecycle from creation to shutdown

Design:
- Coordinates agent initialization and registration
- Monitors agent health and handles failures
- Provides graceful shutdown procedures
- Integrates with AgentRegistry, MessageRouter, and PermissionManager

Usage:
    lifecycle = AgentLifecycleManager(
        registry=registry,
        router=router,
        permissions=permissions
    )

    # Initialize and register agent
    agent = await lifecycle.initialize_agent(metadata)

    # Monitor health
    health = lifecycle.check_agent_health("agent-1")

    # Shutdown agent
    await lifecycle.shutdown_agent("agent-1")

    # Shutdown all agents
    await lifecycle.shutdown_all()
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from .agent import Agent, AgentMetadata, AgentStatus
from .discovery import AgentRegistry, RegistryError
from .messaging import MessageRouter
from .permissions import PermissionManager

logger = logging.getLogger(__name__)


class LifecycleError(Exception):
    """Exception raised for lifecycle management errors."""

    pass


class AgentLifecycleManager:
    """
    Manages the complete lifecycle of agents.

    Provides coordination of agent initialization, registration, monitoring,
    and shutdown procedures. Integrates with core agent subsystems.

    Attributes:
        registry: AgentRegistry for agent discovery
        router: Optional MessageRouter for agent communication
        permissions: Optional PermissionManager for access control
        _shutdown_hooks: Callbacks to execute during shutdown
    """

    def __init__(
        self,
        registry: AgentRegistry,
        router: MessageRouter | None = None,
        permissions: PermissionManager | None = None,
    ) -> None:
        """
        Initialize lifecycle manager.

        Args:
            registry: AgentRegistry for agent management
            router: Optional MessageRouter for communication
            permissions: Optional PermissionManager for access control
        """
        self.registry = registry
        self.router = router
        self.permissions = permissions
        self._shutdown_hooks: list[Callable[..., Any]] = []

        logger.info("Initialized AgentLifecycleManager")

    async def initialize_agent(
        self, metadata: AgentMetadata, auto_register: bool = True, set_ready: bool = True
    ) -> Agent:
        """
        Initialize a new agent.

        Args:
            metadata: AgentMetadata for the agent
            auto_register: Whether to automatically register the agent
            set_ready: Whether to set agent status to READY after initialization

        Returns:
            Initialized Agent instance

        Raises:
            LifecycleError: If initialization fails
        """
        try:
            # Create agent
            agent = Agent(metadata=metadata)

            # Call agent's initialization hook
            await agent.on_initialize()

            # Register agent if requested
            if auto_register:
                self.registry.register_agent(agent)

            # Set to READY status if requested
            if set_ready:
                agent.set_status(AgentStatus.READY)

                # Deliver any queued messages if router available
                if self.router:
                    await self.router.deliver_queued_messages(agent.metadata.agent_id)

            logger.info(f"Initialized agent: {agent.metadata.agent_id}")
            return agent

        except Exception as e:
            raise LifecycleError(f"Failed to initialize agent: {e}") from None

    async def register_agent(self, agent: Agent) -> None:
        """
        Register an existing agent.

        Args:
            agent: Agent instance to register

        Raises:
            LifecycleError: If registration fails
        """
        try:
            self.registry.register_agent(agent)
            logger.info(f"Registered agent: {agent.metadata.agent_id}")
        except RegistryError as e:
            raise LifecycleError(f"Failed to register agent: {e}") from None

    async def shutdown_agent(
        self, agent_id: str, graceful: bool = True, timeout: float = 30.0
    ) -> bool:
        """
        Shutdown an agent gracefully.

        Args:
            agent_id: ID of agent to shutdown
            graceful: Whether to perform graceful shutdown
            timeout: Timeout for graceful shutdown

        Returns:
            True if shutdown successful, False otherwise
        """
        agent = self.registry.get_agent(agent_id)
        if agent is None:
            logger.warning(f"Agent not found for shutdown: {agent_id}")
            return False

        try:
            # Set status to prevent new messages
            agent.set_status(AgentStatus.SHUTDOWN)

            if graceful:
                # Call agent's shutdown hook with timeout
                try:
                    await asyncio.wait_for(agent.on_shutdown(), timeout=timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"Graceful shutdown timeout for agent: {agent_id}")

            # Clear queued messages if router available
            if self.router:
                cleared = self.router.clear_queue(agent_id)
                if cleared > 0:
                    logger.info(f"Cleared {cleared} queued messages for {agent_id}")

            # Remove from registry
            self.registry.deregister_agent(agent_id)

            logger.info(f"Shutdown agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error shutting down agent {agent_id}: {e}")
            return False

    async def shutdown_all(self, graceful: bool = True, timeout: float = 30.0) -> dict[str, bool]:
        """
        Shutdown all agents.

        Args:
            graceful: Whether to perform graceful shutdown
            timeout: Timeout for each agent's graceful shutdown

        Returns:
            Dictionary mapping agent_id to shutdown success status
        """
        agents = self.registry.list_agents()
        results = {}

        logger.info(f"Shutting down {len(agents)} agents...")

        # Shutdown all agents concurrently
        tasks = []
        for agent in agents:
            agent_id = agent.metadata.agent_id
            task = self.shutdown_agent(agent_id, graceful=graceful, timeout=timeout)
            tasks.append((agent_id, task))

        # Wait for all shutdowns
        for agent_id, task in tasks:
            try:
                results[agent_id] = await task
            except Exception as e:
                logger.error(f"Failed to shutdown agent {agent_id}: {e}")
                results[agent_id] = False

        # Execute shutdown hooks
        for hook in self._shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Shutdown hook failed: {e}")

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Shutdown complete: {successful}/{len(results)} agents")

        return results

    def check_agent_health(self, agent_id: str) -> dict[str, Any] | None:
        """
        Check health of an agent.

        Args:
            agent_id: ID of agent to check

        Returns:
            Health information dictionary, or None if agent not found
        """
        agent = self.registry.get_agent(agent_id)
        if agent is None:
            return None

        return agent.get_health()

    def check_all_health(self) -> dict[str, dict[str, Any]]:
        """
        Check health of all agents.

        Returns:
            Dictionary mapping agent_id to health information
        """
        agents = self.registry.list_agents()
        health_report = {}

        for agent in agents:
            agent_id = agent.metadata.agent_id
            health_report[agent_id] = agent.get_health()

        return health_report

    def register_shutdown_hook(self, hook: Callable[..., Any]) -> None:
        """
        Register a callback to be executed during shutdown.

        Args:
            hook: Callable to execute during shutdown (can be async)
        """
        self._shutdown_hooks.append(hook)
        logger.debug(
            f"Registered shutdown hook: {hook.__name__ if hasattr(hook, '__name__') else 'anonymous'}"
        )

    def get_statistics(self) -> dict[str, Any]:
        """
        Get lifecycle manager statistics.

        Returns:
            Dictionary with statistics
        """
        agents = self.registry.list_agents()
        status_counts: dict[str, int] = {}

        for agent in agents:
            status = agent.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_agents": len(agents),
            "by_status": status_counts,
            "shutdown_hooks": len(self._shutdown_hooks),
            "has_router": self.router is not None,
            "has_permissions": self.permissions is not None,
        }

    def __repr__(self) -> str:
        return (
            f"AgentLifecycleManager(agents={len(self.registry)}, hooks={len(self._shutdown_hooks)})"
        )
