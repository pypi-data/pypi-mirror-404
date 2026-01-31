"""
Agent Communication System

Phase 0 Week 3: Core agent communication infrastructure.

This module provides agent discovery, messaging, permissions, and lifecycle management.
"""

from .agent import Agent, AgentMetadata, AgentStatus, AgentType
from .discovery import AgentRegistry, RegistryError
from .lifecycle import AgentLifecycleManager, LifecycleError
from .messaging import Message, MessageResponse, MessageRouter, MessageType, RoutingError
from .permissions import PermissionManager, PermissionRule

__all__ = [
    # Agent model
    "Agent",
    "AgentMetadata",
    "AgentType",
    "AgentStatus",
    # Discovery
    "AgentRegistry",
    "RegistryError",
    # Messaging
    "Message",
    "MessageType",
    "MessageResponse",
    "MessageRouter",
    "RoutingError",
    # Permissions
    "PermissionRule",
    "PermissionManager",
    # Lifecycle
    "AgentLifecycleManager",
    "LifecycleError",
]
