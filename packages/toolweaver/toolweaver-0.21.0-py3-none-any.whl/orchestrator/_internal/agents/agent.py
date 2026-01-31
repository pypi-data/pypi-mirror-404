"""
Agent Model - Core agent representation with metadata and capabilities.

Phase 0 Week 3: Agent Communication
Defines the Agent class with identity, state management, and lifecycle hooks.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Type of agent based on role."""

    EXECUTOR = "executor"  # Executes tasks directly
    COORDINATOR = "coordinator"  # Coordinates other agents
    SPECIALIST = "specialist"  # Domain-specialized expert
    MONITOR = "monitor"  # Observes and reports


class AgentStatus(Enum):
    """Current status of agent."""

    INITIALIZED = "initialized"  # Just created
    READY = "ready"  # Ready for work
    BUSY = "busy"  # Currently processing
    ERROR = "error"  # Error state
    SHUTDOWN = "shutdown"  # Shut down


@dataclass
class AgentMetadata:
    """
    Agent identity and capabilities.

    Contains all information needed to identify and categorize an agent,
    including what it can do and what tools it has access to.
    """

    agent_id: str  # Unique identifier (e.g., "researcher_001")
    name: str  # Human-readable name
    type: AgentType  # Type (executor, coordinator, specialist, monitor)
    domain: str  # Domain expertise (research, coding, analysis, etc.)
    capabilities: list[str]  # What the agent can do
    tools: list[str] = field(default_factory=list)  # Available tools
    description: str = ""  # Purpose and description
    metadata: dict[str, Any] = field(default_factory=dict)  # Custom metadata

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not isinstance(self.type, AgentType):
            raise ValueError(f"type must be AgentType enum, got {type(self.type)}")
        if not self.domain:
            raise ValueError("domain cannot be empty")
        if not self.capabilities:
            raise ValueError("capabilities cannot be empty")


class Agent:
    """
    Core agent with lifecycle and messaging capabilities.

    Represents an agent in the system with:
    - Identity and capabilities (via AgentMetadata)
    - State management (persistent and transient)
    - Lifecycle hooks (on_initialize, on_message, on_shutdown)
    - Integration with ProfileLoader for configuration
    """

    def __init__(
        self,
        metadata: AgentMetadata,
        profile: dict[str, Any] | None = None,
        storage_backend: Any = None,
    ) -> None:
        """
        Initialize agent with metadata and optional profile.

        Args:
            metadata: Agent identity and capabilities
            profile: Agent profile from ProfileLoader (optional)
            storage_backend: Phase -1 StorageBackend for state persistence
        """
        self.metadata = metadata
        self.profile = profile or {}
        self.storage = storage_backend

        # Agent state
        self.state: dict[str, Any] = {}
        self.status = AgentStatus.INITIALIZED
        self.created_at = time.time()
        self.last_activity = time.time()

        # Message tracking
        self.messages_sent = 0
        self.messages_received = 0
        self.error_count = 0

        # Lifecycle hooks (can be overridden by subclasses)
        self._on_initialize_hooks: list[Callable[..., Any]] = []
        self._on_message_hooks: list[Callable[..., Any]] = []
        self._on_shutdown_hooks: list[Callable[..., Any]] = []

        logger.info(
            f"Agent created: {self.metadata.agent_id} "
            f"(type={self.metadata.type.value}, domain={self.metadata.domain})"
        )

    @property
    def agent_id(self) -> str:
        """Get agent ID."""
        return self.metadata.agent_id

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.metadata.name

    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return self.metadata.type

    @property
    def uptime(self) -> float:
        """Get agent uptime in seconds."""
        return time.time() - self.created_at

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities."""
        return self.metadata.capabilities.copy()

    def has_capability(self, capability: str) -> bool:
        """Check if agent has specific capability."""
        return capability in self.metadata.capabilities

    def get_tools(self) -> list[str]:
        """Get list of available tools."""
        return self.metadata.tools.copy()

    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has access to specific tool."""
        return tool_name in self.metadata.tools

    # State management

    def update_state(self, key: str, value: Any, persist: bool = False) -> None:
        """
        Update agent state.

        Args:
            key: State key
            value: State value
            persist: If True, persist to StorageBackend
        """
        self.state[key] = value
        self.last_activity = time.time()

        if persist and self.storage:
            try:
                self.storage.save(f"agent_state:{self.agent_id}", key, value)
                logger.debug(f"Persisted state: {self.agent_id}.{key}")
            except Exception as e:
                logger.error(f"Failed to persist state: {e}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.state.get(key, default)

    def clear_state(self, persist: bool = False) -> None:
        """Clear all agent state."""
        self.state.clear()

        if persist and self.storage:
            try:
                self.storage.delete(f"agent_state:{self.agent_id}")
                logger.debug(f"Cleared persisted state: {self.agent_id}")
            except Exception as e:
                logger.error(f"Failed to clear persisted state: {e}")

    async def load_state(self) -> bool:
        """
        Load agent state from StorageBackend.

        Returns:
            True if state was loaded, False otherwise
        """
        if not self.storage:
            return False

        try:
            state_data = await self.storage.load(f"agent_state:{self.agent_id}")
            if state_data:
                self.state = state_data
                logger.info(f"Loaded state for agent: {self.agent_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

        return False

    # Status management

    def set_status(self, status: AgentStatus) -> None:
        """
        Update agent status.

        Args:
            status: New status
        """
        old_status = self.status
        self.status = status
        self.last_activity = time.time()

        logger.info(f"Agent status changed: {self.agent_id} {old_status.value} → {status.value}")

    def is_ready(self) -> bool:
        """Check if agent is ready for work."""
        return self.status == AgentStatus.READY

    def is_busy(self) -> bool:
        """Check if agent is currently busy."""
        return self.status == AgentStatus.BUSY

    def is_shutdown(self) -> bool:
        """Check if agent is shut down."""
        return self.status == AgentStatus.SHUTDOWN

    # Lifecycle hooks

    def add_initialize_hook(self, hook: Callable[..., Any]) -> None:
        """Add hook to be called on initialization."""
        self._on_initialize_hooks.append(hook)

    def add_message_hook(self, hook: Callable[..., Any]) -> None:
        """Add hook to be called when message is received."""
        self._on_message_hooks.append(hook)

    def add_shutdown_hook(self, hook: Callable[..., Any]) -> None:
        """Add hook to be called on shutdown."""
        self._on_shutdown_hooks.append(hook)

    async def on_initialize(self) -> None:
        """
        Called when agent is initialized.

        Override in subclasses or add hooks for custom initialization logic.
        """
        logger.info(f"Initializing agent: {self.agent_id}")

        # Call registered hooks
        for hook in self._on_initialize_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self)
                else:
                    hook(self)
            except Exception as e:
                logger.error(f"Initialize hook failed: {e}")

        # Load persisted state if available
        await self.load_state()

        self.set_status(AgentStatus.READY)

    async def on_message(self, message: Any) -> Any:
        """
        Called when agent receives a message.

        Override in subclasses for custom message handling logic.

        Args:
            message: Message object

        Returns:
            Response to the message
        """
        logger.debug(f"Agent {self.agent_id} received message: {message}")

        self.messages_received += 1
        self.last_activity = time.time()

        # Call registered hooks
        for hook in self._on_message_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self, message)
                else:
                    hook(self, message)
            except Exception as e:
                logger.error(f"Message hook failed: {e}")

        # Default: return acknowledgment
        return {"status": "received", "agent_id": self.agent_id}

    async def on_shutdown(self) -> None:
        """
        Called when agent is shutting down.

        Override in subclasses or add hooks for custom cleanup logic.
        """
        logger.info(f"Shutting down agent: {self.agent_id}")

        # Call registered hooks
        for hook in self._on_shutdown_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self)
                else:
                    hook(self)
            except Exception as e:
                logger.error(f"Shutdown hook failed: {e}")

        # Persist state before shutdown
        if self.storage and self.state:
            try:
                await self.storage.save(f"agent_state:{self.agent_id}", "state", self.state)
                logger.debug(f"Persisted state on shutdown: {self.agent_id}")
            except Exception as e:
                logger.error(f"Failed to persist state on shutdown: {e}")

        self.set_status(AgentStatus.SHUTDOWN)

    # Error handling

    def record_error(self, error: Exception) -> None:
        """
        Record an error.

        Args:
            error: Exception that occurred
        """
        self.error_count += 1
        self.last_activity = time.time()

        logger.error(f"Agent error: {self.agent_id} - {error}")

        if self.status != AgentStatus.ERROR:
            self.set_status(AgentStatus.ERROR)

    def reset_error_state(self) -> None:
        """Reset agent from error state to ready."""
        if self.status == AgentStatus.ERROR:
            self.set_status(AgentStatus.READY)
            logger.info(f"Agent recovered from error: {self.agent_id}")

    # Health and metrics

    def get_health(self) -> dict[str, Any]:
        """
        Get agent health status.

        Returns:
            Health information dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "domain": self.metadata.domain,
            "status": self.status.value,
            "uptime": self.uptime,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "error_count": self.error_count,
            "last_activity": self.last_activity,
            "state_keys": list(self.state.keys()),
        }

    # Utility methods

    def to_dict(self) -> dict[str, Any]:
        """
        Convert agent to dictionary representation.

        Returns:
            Dictionary with agent information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "domain": self.metadata.domain,
            "capabilities": self.get_capabilities(),
            "tools": self.get_tools(),
            "description": self.metadata.description,
            "status": self.status.value,
            "uptime": self.uptime,
            "metadata": self.metadata.metadata,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Agent(id={self.agent_id}, type={self.agent_type.value}, "
            f"domain={self.metadata.domain}, status={self.status.value})"
        )

    def __str__(self) -> str:
        """Human-readable string."""
        return f"{self.name} ({self.agent_id})"
