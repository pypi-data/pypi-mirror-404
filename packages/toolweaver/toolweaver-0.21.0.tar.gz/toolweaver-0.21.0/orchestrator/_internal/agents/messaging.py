"""
Message Routing System

Provides message passing and routing capabilities for agent communication.
Supports request/response, broadcast, and notification patterns.

Components:
- Message: Message data structure with type, sender, recipient, payload
- MessageType: Enum for different message types (REQUEST, RESPONSE, BROADCAST, NOTIFICATION)
- MessageResponse: Response wrapper with status and result
- MessageRouter: Routes messages between agents with queue management

Design:
- Asynchronous message passing with callback-based delivery
- Queue-based message buffering for offline agents
- Support for point-to-point and broadcast communication
- Integration with Agent lifecycle hooks for message handling

Usage:
    router = MessageRouter(registry=registry)

    # Send a request message
    response = await router.send_message(
        from_agent="agent-1",
        to_agent="agent-2",
        message_type=MessageType.REQUEST,
        payload={"action": "search", "query": "test"}
    )

    # Broadcast to all agents
    responses = await router.broadcast_message(
        from_agent="coordinator",
        message_type=MessageType.NOTIFICATION,
        payload={"event": "system_update"}
    )
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .agent import Agent, AgentStatus
from .discovery import AgentRegistry

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be sent between agents."""

    REQUEST = "request"  # Request expecting a response
    RESPONSE = "response"  # Response to a request
    BROADCAST = "broadcast"  # Broadcast to multiple agents
    NOTIFICATION = "notification"  # One-way notification


@dataclass
class Message:
    """
    Message structure for agent communication.

    Attributes:
        message_id: Unique message identifier
        message_type: Type of message (request, response, broadcast, notification)
        from_agent: Sender agent ID
        to_agent: Recipient agent ID (None for broadcasts)
        payload: Message payload (arbitrary data)
        timestamp: Message creation timestamp
        correlation_id: ID linking request/response pairs
        metadata: Additional message metadata
    """

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    from_agent: str = ""
    to_agent: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=MessageType(data.get("message_type", "request")),
            from_agent=data.get("from_agent", ""),
            to_agent=data.get("to_agent"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time()),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MessageResponse:
    """
    Response wrapper for message handling.

    Attributes:
        success: Whether message was handled successfully
        result: Result data from message handler
        error: Error message if unsuccessful
        metadata: Additional response metadata
    """

    success: bool
    result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class RoutingError(Exception):
    """Exception raised for message routing errors."""

    pass


class MessageRouter:
    """
    Routes messages between agents with queue management.

    Provides message delivery with support for:
    - Point-to-point messaging (request/response)
    - Broadcast messaging (one-to-many)
    - Message queuing for offline agents
    - Asynchronous message delivery

    Attributes:
        registry: AgentRegistry for agent lookup
        _message_queues: Queues for buffering messages to offline agents
        _pending_responses: Pending response callbacks for requests
        _message_history: History of sent messages
    """

    def __init__(self, registry: AgentRegistry) -> None:
        """
        Initialize message router.

        Args:
            registry: AgentRegistry for agent discovery and lookup
        """
        self.registry = registry
        self._message_queues: dict[str, list[Message]] = {}
        self._pending_responses: dict[str, asyncio.Future[Any]] = {}
        self._message_history: list[Message] = []
        self._max_history = 1000  # Maximum messages to keep in history

        logger.info("Initialized MessageRouter")

    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        payload: dict[str, Any],
        correlation_id: str | None = None,
        timeout: float = 30.0,
    ) -> MessageResponse:
        """
        Send a message from one agent to another.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            message_type: Type of message
            payload: Message payload
            correlation_id: Optional correlation ID for request/response pairing
            timeout: Timeout for waiting for response (for REQUEST messages)

        Returns:
            MessageResponse with result or error

        Raises:
            RoutingError: If routing fails
        """
        # Validate sender exists
        sender = self.registry.get_agent(from_agent)
        if sender is None:
            raise RoutingError(f"Sender agent not found: {from_agent}")

        # Validate recipient exists
        recipient = self.registry.get_agent(to_agent)
        if recipient is None:
            raise RoutingError(f"Recipient agent not found: {to_agent}")

        # Create message
        message = Message(
            message_type=message_type,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

        # Add to history
        self._add_to_history(message)

        # Update sender's sent count
        sender.messages_sent += 1

        # Deliver message
        try:
            if recipient.status == AgentStatus.READY:
                # Deliver immediately if recipient is ready
                result = await self._deliver_message(recipient, message)
                return MessageResponse(success=True, result=result)
            else:
                # Queue message if recipient is not ready
                self._queue_message(to_agent, message)
                logger.info(f"Queued message from {from_agent} to {to_agent} (recipient not ready)")
                return MessageResponse(success=True, result=None, metadata={"queued": True})
        except Exception as e:
            logger.error(f"Failed to deliver message from {from_agent} to {to_agent}: {e}")
            return MessageResponse(success=False, error=str(e))

    async def broadcast_message(
        self,
        from_agent: str,
        message_type: MessageType,
        payload: dict[str, Any],
        agent_filter: Callable[[Agent], bool] | None = None,
    ) -> list[MessageResponse]:
        """
        Broadcast a message to multiple agents.

        Args:
            from_agent: Sender agent ID
            message_type: Type of message
            payload: Message payload
            agent_filter: Optional filter function to select recipients

        Returns:
            List of MessageResponse from each recipient

        Raises:
            RoutingError: If sender not found
        """
        # Validate sender exists
        sender = self.registry.get_agent(from_agent)
        if sender is None:
            raise RoutingError(f"Sender agent not found: {from_agent}")

        # Get recipients (all agents except sender)
        recipients = [
            agent for agent in self.registry.list_agents() if agent.metadata.agent_id != from_agent
        ]

        # Apply filter if provided
        if agent_filter:
            recipients = [agent for agent in recipients if agent_filter(agent)]

        # Create and send messages
        responses = []
        for recipient in recipients:
            message = Message(
                message_type=message_type,
                from_agent=from_agent,
                to_agent=recipient.metadata.agent_id,
                payload=payload,
            )

            self._add_to_history(message)
            sender.messages_sent += 1

            try:
                if recipient.status == AgentStatus.READY:
                    result = await self._deliver_message(recipient, message)
                    responses.append(MessageResponse(success=True, result=result))
                else:
                    self._queue_message(recipient.metadata.agent_id, message)
                    responses.append(
                        MessageResponse(success=True, result=None, metadata={"queued": True})
                    )
            except Exception as e:
                logger.error(f"Failed to deliver broadcast to {recipient.metadata.agent_id}: {e}")
                responses.append(MessageResponse(success=False, error=str(e)))

        logger.info(f"Broadcast from {from_agent} to {len(recipients)} agents")
        return responses

    async def _deliver_message(self, recipient: Agent, message: Message) -> Any:
        """
        Deliver a message to an agent by calling its on_message hook.

        Args:
            recipient: Agent to receive message
            message: Message to deliver

        Returns:
            Result from agent's message handler
        """
        try:
            result = await recipient.on_message(message.to_dict())
            logger.debug(f"Delivered message {message.message_id} to {recipient.metadata.agent_id}")
            return result
        except Exception as e:
            logger.error(f"Error delivering message to {recipient.metadata.agent_id}: {e}")
            raise

    def _queue_message(self, agent_id: str, message: Message) -> None:
        """Queue a message for an agent."""
        if agent_id not in self._message_queues:
            self._message_queues[agent_id] = []
        self._message_queues[agent_id].append(message)
        logger.debug(
            f"Queued message for {agent_id} (queue size: {len(self._message_queues[agent_id])})"
        )

    async def deliver_queued_messages(self, agent_id: str) -> int:
        """
        Deliver all queued messages for an agent.

        Args:
            agent_id: Agent ID to deliver queued messages to

        Returns:
            Number of messages delivered

        Raises:
            RoutingError: If agent not found
        """
        agent = self.registry.get_agent(agent_id)
        if agent is None:
            raise RoutingError(f"Agent not found: {agent_id}")

        if agent_id not in self._message_queues:
            return 0

        messages = self._message_queues.pop(agent_id)
        delivered = 0

        for message in messages:
            try:
                await self._deliver_message(agent, message)
                delivered += 1
            except Exception as e:
                logger.error(f"Failed to deliver queued message to {agent_id}: {e}")

        logger.info(f"Delivered {delivered}/{len(messages)} queued messages to {agent_id}")
        return delivered

    def get_queue_size(self, agent_id: str) -> int:
        """Get number of queued messages for an agent."""
        return len(self._message_queues.get(agent_id, []))

    def clear_queue(self, agent_id: str) -> int:
        """
        Clear all queued messages for an agent.

        Args:
            agent_id: Agent ID to clear queue for

        Returns:
            Number of messages cleared
        """
        if agent_id in self._message_queues:
            count = len(self._message_queues[agent_id])
            del self._message_queues[agent_id]
            logger.info(f"Cleared {count} queued messages for {agent_id}")
            return count
        return 0

    def _add_to_history(self, message: Message) -> None:
        """Add message to history with size limit."""
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

    def get_message_history(self, agent_id: str | None = None, limit: int = 100) -> list[Message]:
        """
        Get message history, optionally filtered by agent.

        Args:
            agent_id: Optional agent ID to filter by (sender or recipient)
            limit: Maximum number of messages to return

        Returns:
            List of Message instances
        """
        messages = self._message_history

        if agent_id:
            messages = [m for m in messages if m.from_agent == agent_id or m.to_agent == agent_id]

        return messages[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get router statistics.

        Returns:
            Dictionary with router statistics
        """
        total_queued = sum(len(queue) for queue in self._message_queues.values())

        return {
            "total_messages": len(self._message_history),
            "queued_messages": total_queued,
            "agents_with_queues": len(self._message_queues),
            "history_size": len(self._message_history),
            "max_history": self._max_history,
        }

    def clear_history(self) -> None:
        """Clear message history."""
        count = len(self._message_history)
        self._message_history.clear()
        logger.info(f"Cleared message history ({count} messages)")

    def __repr__(self) -> str:
        return f"MessageRouter(messages={len(self._message_history)}, queued={sum(len(q) for q in self._message_queues.values())})"
