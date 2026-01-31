"""
Tests for the Agent Communication System.

Verifies agent communication and lifecycle features:
1. Agent Model (agent.py)
2. Agent Discovery (discovery.py)
3. Message Routing (messaging.py)
4. Permission System (permissions.py)
5. Lifecycle Management (lifecycle.py)
"""

from typing import Any

import pytest

from orchestrator._internal.agents import (
    Agent,
    AgentMetadata,
    AgentStatus,
    AgentType,
)

# =============================================================================
# Agent Model Tests (5 tests)
# =============================================================================


class TestAgentModel:
    """Tests for Agent class and AgentMetadata."""

    def test_agent_metadata_creation(self) -> None:
        """Test creating agent metadata with all required fields."""
        metadata = AgentMetadata(
            agent_id="test_001",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test", "validate"],
            tools=["test_tool"],
            description="A test agent",
            metadata={"version": "1.0"},
        )

        assert metadata.agent_id == "test_001"
        assert metadata.name == "Test Agent"
        assert metadata.type == AgentType.EXECUTOR
        assert metadata.domain == "testing"
        assert "test" in metadata.capabilities
        assert "test_tool" in metadata.tools
        assert metadata.description == "A test agent"
        assert metadata.metadata["version"] == "1.0"

    def test_agent_metadata_validation(self) -> None:
        """Test that AgentMetadata validates required fields."""
        # Missing agent_id
        with pytest.raises(ValueError, match="agent_id"):
            AgentMetadata(
                agent_id="",
                name="Test",
                type=AgentType.EXECUTOR,
                domain="test",
                capabilities=["test"],
            )

        # Missing name
        with pytest.raises(ValueError, match="name"):
            AgentMetadata(
                agent_id="test_001",
                name="",
                type=AgentType.EXECUTOR,
                domain="test",
                capabilities=["test"],
            )

        # Missing domain
        with pytest.raises(ValueError, match="domain"):
            AgentMetadata(
                agent_id="test_001",
                name="Test",
                type=AgentType.EXECUTOR,
                domain="",
                capabilities=["test"],
            )

        # Missing capabilities
        with pytest.raises(ValueError, match="capabilities"):
            AgentMetadata(
                agent_id="test_001",
                name="Test",
                type=AgentType.EXECUTOR,
                domain="test",
                capabilities=[],
            )

    def test_agent_creation(self) -> None:
        """Test creating agent with metadata."""
        metadata = AgentMetadata(
            agent_id="agent_001",
            name="Research Agent",
            type=AgentType.SPECIALIST,
            domain="research",
            capabilities=["search", "analyze"],
            tools=["web_search", "summarizer"],
            description="Research specialist",
        )

        agent = Agent(metadata)

        assert agent.agent_id == "agent_001"
        assert agent.name == "Research Agent"
        assert agent.agent_type == AgentType.SPECIALIST
        assert agent.status == AgentStatus.INITIALIZED
        assert agent.messages_sent == 0
        assert agent.messages_received == 0
        assert agent.error_count == 0
        assert agent.uptime >= 0

    def test_agent_state_management(self) -> None:
        """Test agent state management (get, set, clear)."""
        metadata = AgentMetadata(
            agent_id="test_002",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        agent = Agent(metadata)

        # Set state
        agent.update_state("task_count", 5)
        agent.update_state("last_task", "task_123")

        # Get state
        assert agent.get_state("task_count") == 5
        assert agent.get_state("last_task") == "task_123"
        assert agent.get_state("nonexistent") is None
        assert agent.get_state("nonexistent", "default") == "default"

        # Clear state
        agent.clear_state()
        assert agent.get_state("task_count") is None
        assert len(agent.state) == 0

    def test_agent_status_transitions(self) -> None:
        """Test agent status transitions."""
        metadata = AgentMetadata(
            agent_id="test_003",
            name="Test Agent",
            type=AgentType.COORDINATOR,
            domain="testing",
            capabilities=["coordinate"],
        )
        agent = Agent(metadata)

        # Initial status
        assert agent.status == AgentStatus.INITIALIZED
        assert not agent.is_ready()
        assert not agent.is_busy()
        assert not agent.is_shutdown()

        # Transition to ready
        agent.set_status(AgentStatus.READY)
        assert agent.is_ready()

        # Transition to busy
        agent.set_status(AgentStatus.BUSY)
        assert agent.is_busy()
        # Status is mutable, can't be checked with == after set_status
        assert agent.is_busy()  # Verify through method instead

        # Transition to error
        agent.set_status(AgentStatus.ERROR)
        # Status is mutable, verify through status attribute access
        assert agent.status.value == AgentStatus.ERROR.value

        # Reset from error
        agent.reset_error_state()
        assert agent.is_ready()

        # Transition to shutdown
        agent.set_status(AgentStatus.SHUTDOWN)
        assert agent.is_shutdown()

    def test_agent_capabilities_and_tools(self) -> None:
        """Test agent capabilities and tools methods."""
        metadata = AgentMetadata(
            agent_id="test_004",
            name="Test Agent",
            type=AgentType.SPECIALIST,
            domain="coding",
            capabilities=["code", "debug", "refactor"],
            tools=["linter", "debugger", "formatter"],
        )
        agent = Agent(metadata)

        # Get capabilities
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 3
        assert "code" in capabilities
        assert "debug" in capabilities

        # Check capability
        assert agent.has_capability("code")
        assert agent.has_capability("debug")
        assert not agent.has_capability("nonexistent")

        # Get tools
        tools = agent.get_tools()
        assert len(tools) == 3
        assert "linter" in tools

        # Check tool
        assert agent.has_tool("linter")
        assert agent.has_tool("debugger")
        assert not agent.has_tool("nonexistent")

    @pytest.mark.asyncio
    async def test_agent_lifecycle_hooks(self) -> None:
        """Test agent lifecycle hooks (initialize, message, shutdown)."""
        metadata = AgentMetadata(
            agent_id="test_005",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        agent = Agent(metadata)

        # Track hook calls
        hooks_called = {"initialize": False, "message": False, "shutdown": False}

        def init_hook(agent: Agent) -> None:
            hooks_called["initialize"] = True

        def message_hook(agent: Agent, message: dict[str, Any]) -> None:
            hooks_called["message"] = True

        def shutdown_hook(agent: Agent) -> None:
            hooks_called["shutdown"] = True

        # Add hooks
        agent.add_initialize_hook(init_hook)
        agent.add_message_hook(message_hook)
        agent.add_shutdown_hook(shutdown_hook)

        # Call lifecycle methods
        await agent.on_initialize()
        assert hooks_called["initialize"]
        assert agent.is_ready()

        await agent.on_message({"test": "message"})
        assert hooks_called["message"]
        assert agent.messages_received == 1

        await agent.on_shutdown()
        assert hooks_called["shutdown"]
        assert agent.is_shutdown()

    def test_agent_error_handling(self) -> None:
        """Test agent error recording and recovery."""
        metadata = AgentMetadata(
            agent_id="test_006",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        agent = Agent(metadata)
        agent.set_status(AgentStatus.READY)

        # Record error
        agent.record_error(Exception("Test error"))
        assert agent.error_count == 1
        assert agent.status == AgentStatus.ERROR

        # Record another error
        agent.record_error(Exception("Another error"))
        assert agent.error_count == 2
        assert agent.status == AgentStatus.ERROR

        # Reset error state
        agent.reset_error_state()
        assert agent.is_ready()
        assert agent.error_count == 2  # Error count persists

    def test_agent_health_check(self) -> None:
        """Test agent health check returns correct information."""
        metadata = AgentMetadata(
            agent_id="test_007",
            name="Test Agent",
            type=AgentType.MONITOR,
            domain="monitoring",
            capabilities=["monitor", "alert"],
        )
        agent = Agent(metadata)
        agent.set_status(AgentStatus.READY)
        agent.update_state("monitored_agents", 5)

        health = agent.get_health()

        assert health["agent_id"] == "test_007"
        assert health["name"] == "Test Agent"
        assert health["type"] == "monitor"
        assert health["domain"] == "monitoring"
        assert health["status"] == "ready"
        assert health["uptime"] >= 0
        assert health["messages_sent"] == 0
        assert health["messages_received"] == 0
        assert health["error_count"] == 0
        assert "monitored_agents" in health["state_keys"]

    def test_agent_to_dict(self) -> None:
        """Test agent to_dict conversion."""
        metadata = AgentMetadata(
            agent_id="test_008",
            name="Test Agent",
            type=AgentType.COORDINATOR,
            domain="coordination",
            capabilities=["coordinate", "delegate"],
            tools=["router", "scheduler"],
            description="Coordination specialist",
            metadata={"version": "1.0", "priority": "high"},
        )
        agent = Agent(metadata)

        agent_dict = agent.to_dict()

        assert agent_dict["agent_id"] == "test_008"
        assert agent_dict["name"] == "Test Agent"
        assert agent_dict["type"] == "coordinator"
        assert agent_dict["domain"] == "coordination"
        assert "coordinate" in agent_dict["capabilities"]
        assert "router" in agent_dict["tools"]
        assert agent_dict["description"] == "Coordination specialist"
        assert agent_dict["status"] == "initialized"
        assert agent_dict["metadata"]["version"] == "1.0"


# =============================================================================
# Placeholder test classes for remaining components
# =============================================================================


class TestAgentDiscovery:
    """Tests for AgentRegistry and agent discovery."""

    def test_registry_initialization(self) -> None:
        """Test registry initialization."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()
        assert len(registry) == 0
        assert registry.list_agents() == []

    def test_agent_registration(self) -> None:
        """Test agent registration and deregistration."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create and register agent
        metadata = AgentMetadata(
            agent_id="test-agent-1",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
            tools=["test_tool"],
        )
        agent = Agent(metadata=metadata)

        registry.register_agent(agent)
        assert len(registry) == 1
        assert "test-agent-1" in registry

        # Retrieve agent
        retrieved = registry.get_agent("test-agent-1")
        assert retrieved is agent

        # Deregister agent
        assert registry.deregister_agent("test-agent-1") is True
        assert len(registry) == 0
        assert "test-agent-1" not in registry

    def test_find_agents_by_type(self) -> None:
        """Test finding agents by type."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create agents of different types
        executor = Agent(
            metadata=AgentMetadata(
                agent_id="executor-1",
                name="Executor",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["execute"],
            )
        )
        coordinator = Agent(
            metadata=AgentMetadata(
                agent_id="coordinator-1",
                name="Coordinator",
                type=AgentType.COORDINATOR,
                domain="general",
                capabilities=["coordinate"],
            )
        )

        registry.register_agent(executor)
        registry.register_agent(coordinator)

        # Find by type
        executors = registry.find_agents_by_type(AgentType.EXECUTOR)
        assert len(executors) == 1
        assert executors[0].metadata.agent_id == "executor-1"

        coordinators = registry.find_agents_by_type(AgentType.COORDINATOR)
        assert len(coordinators) == 1
        assert coordinators[0].metadata.agent_id == "coordinator-1"

    def test_find_agents_by_capability(self) -> None:
        """Test finding agents by capability."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create agents with different capabilities
        agent1 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-1",
                name="Agent 1",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["search", "analyze"],
            )
        )
        agent2 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-2",
                name="Agent 2",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["search", "write"],
            )
        )

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        # Find by capability
        search_agents = registry.find_agents_by_capability("search")
        assert len(search_agents) == 2

        analyze_agents = registry.find_agents_by_capability("analyze")
        assert len(analyze_agents) == 1
        assert analyze_agents[0].metadata.agent_id == "agent-1"

    def test_find_agents_by_domain(self) -> None:
        """Test finding agents by domain."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create agents in different domains
        code_agent = Agent(
            metadata=AgentMetadata(
                agent_id="code-1",
                name="Code Agent",
                type=AgentType.EXECUTOR,
                domain="code",
                capabilities=["code_analysis"],
            )
        )
        data_agent = Agent(
            metadata=AgentMetadata(
                agent_id="data-1",
                name="Data Agent",
                type=AgentType.EXECUTOR,
                domain="data",
                capabilities=["data_processing"],
            )
        )

        registry.register_agent(code_agent)
        registry.register_agent(data_agent)

        # Find by domain
        code_agents = registry.find_agents_by_domain("code")
        assert len(code_agents) == 1
        assert code_agents[0].metadata.agent_id == "code-1"

        data_agents = registry.find_agents_by_domain("data")
        assert len(data_agents) == 1
        assert data_agents[0].metadata.agent_id == "data-1"

    def test_find_agents_multi_criteria(self) -> None:
        """Test finding agents with multiple criteria."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create diverse agents
        agent1 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-1",
                name="Agent 1",
                type=AgentType.EXECUTOR,
                domain="code",
                capabilities=["search", "analyze"],
                tools=["git"],
            )
        )
        agent2 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-2",
                name="Agent 2",
                type=AgentType.COORDINATOR,
                domain="code",
                capabilities=["coordinate"],
                tools=["git"],
            )
        )
        agent3 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-3",
                name="Agent 3",
                type=AgentType.EXECUTOR,
                domain="data",
                capabilities=["search"],
                tools=["database"],
            )
        )

        registry.register_agent(agent1)
        registry.register_agent(agent2)
        registry.register_agent(agent3)

        # Find by multiple criteria
        code_executors = registry.find_agents(agent_type=AgentType.EXECUTOR, domain="code")
        assert len(code_executors) == 1
        assert code_executors[0].metadata.agent_id == "agent-1"

        git_agents = registry.find_agents(tool="git", capability="search")
        assert len(git_agents) == 1
        assert git_agents[0].metadata.agent_id == "agent-1"

    def test_registry_statistics(self) -> None:
        """Test registry statistics."""
        from orchestrator._internal.agents.discovery import AgentRegistry

        registry = AgentRegistry()

        # Create and register agents
        for i in range(3):
            agent = Agent(
                metadata=AgentMetadata(
                    agent_id=f"agent-{i}",
                    name=f"Agent {i}",
                    type=AgentType.EXECUTOR if i < 2 else AgentType.COORDINATOR,
                    domain="general",
                    capabilities=["test"],
                )
            )
            registry.register_agent(agent)

        stats = registry.get_statistics()
        assert stats["total_agents"] == 3
        assert stats["by_type"]["executor"] == 2
        assert stats["by_type"]["coordinator"] == 1
        assert stats["capabilities"] == 1
        assert stats["domains"] == 1


class TestMessageRouting:
    """Tests for MessageRouter and message patterns."""

    @pytest.mark.asyncio
    async def test_message_creation(self) -> None:
        """Test message creation and serialization."""
        from orchestrator._internal.agents.messaging import Message, MessageType

        message = Message(
            message_type=MessageType.REQUEST,
            from_agent="agent-1",
            to_agent="agent-2",
            payload={"action": "test"},
            correlation_id="test-123",
        )

        assert message.message_type == MessageType.REQUEST
        assert message.from_agent == "agent-1"
        assert message.to_agent == "agent-2"
        assert message.payload["action"] == "test"
        assert message.correlation_id == "test-123"

        # Test to_dict
        message_dict = message.to_dict()
        assert message_dict["message_type"] == "request"
        assert message_dict["from_agent"] == "agent-1"

        # Test from_dict
        reconstructed = Message.from_dict(message_dict)
        assert reconstructed.message_type == MessageType.REQUEST
        assert reconstructed.from_agent == "agent-1"

    @pytest.mark.asyncio
    async def test_router_initialization(self) -> None:
        """Test router initialization."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        stats = router.get_statistics()
        assert stats["total_messages"] == 0
        assert stats["queued_messages"] == 0

    @pytest.mark.asyncio
    async def test_send_message(self) -> None:
        """Test sending message between agents."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter, MessageType

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        # Create and register agents
        sender = Agent(
            metadata=AgentMetadata(
                agent_id="sender",
                name="Sender",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["send"],
            )
        )
        receiver = Agent(
            metadata=AgentMetadata(
                agent_id="receiver",
                name="Receiver",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["receive"],
            )
        )

        # Set receiver to READY status
        receiver.set_status(AgentStatus.READY)

        registry.register_agent(sender)
        registry.register_agent(receiver)

        # Send message
        response = await router.send_message(
            from_agent="sender",
            to_agent="receiver",
            message_type=MessageType.REQUEST,
            payload={"action": "test"},
        )

        assert response.success is True
        assert sender.messages_sent == 1
        assert receiver.messages_received == 1

    @pytest.mark.asyncio
    async def test_message_queuing(self) -> None:
        """Test message queuing for non-ready agents."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter, MessageType

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        # Create and register agents (receiver in INITIALIZED state)
        sender = Agent(
            metadata=AgentMetadata(
                agent_id="sender",
                name="Sender",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["send"],
            )
        )
        receiver = Agent(
            metadata=AgentMetadata(
                agent_id="receiver",
                name="Receiver",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["receive"],
            )
        )

        registry.register_agent(sender)
        registry.register_agent(receiver)

        # Send message (should be queued)
        response = await router.send_message(
            from_agent="sender",
            to_agent="receiver",
            message_type=MessageType.REQUEST,
            payload={"action": "test"},
        )

        assert response.success is True
        assert response.metadata.get("queued") is True
        assert router.get_queue_size("receiver") == 1
        assert receiver.messages_received == 0  # Not delivered yet

        # Make receiver ready and deliver queued messages
        receiver.set_status(AgentStatus.READY)
        delivered = await router.deliver_queued_messages("receiver")

        assert delivered == 1
        assert router.get_queue_size("receiver") == 0
        assert receiver.messages_received == 1

    @pytest.mark.asyncio
    async def test_broadcast_message(self) -> None:
        """Test broadcasting message to multiple agents."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter, MessageType

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        # Create and register multiple agents
        sender = Agent(
            metadata=AgentMetadata(
                agent_id="broadcaster",
                name="Broadcaster",
                type=AgentType.COORDINATOR,
                domain="general",
                capabilities=["broadcast"],
            )
        )

        receivers = []
        for i in range(3):
            agent = Agent(
                metadata=AgentMetadata(
                    agent_id=f"receiver-{i}",
                    name=f"Receiver {i}",
                    type=AgentType.EXECUTOR,
                    domain="general",
                    capabilities=["receive"],
                )
            )
            agent.set_status(AgentStatus.READY)
            receivers.append(agent)

        registry.register_agent(sender)
        for receiver in receivers:
            registry.register_agent(receiver)

        # Broadcast message
        responses = await router.broadcast_message(
            from_agent="broadcaster",
            message_type=MessageType.BROADCAST,
            payload={"announcement": "test"},
        )

        assert len(responses) == 3  # All receivers
        assert all(r.success for r in responses)
        assert sender.messages_sent == 3
        assert all(r.messages_received == 1 for r in receivers)

    @pytest.mark.asyncio
    async def test_broadcast_with_filter(self) -> None:
        """Test broadcasting with agent filter."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter, MessageType

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        # Create sender
        sender = Agent(
            metadata=AgentMetadata(
                agent_id="sender",
                name="Sender",
                type=AgentType.COORDINATOR,
                domain="general",
                capabilities=["broadcast"],
            )
        )

        # Create receivers in different domains
        code_agent = Agent(
            metadata=AgentMetadata(
                agent_id="code-agent",
                name="Code Agent",
                type=AgentType.EXECUTOR,
                domain="code",
                capabilities=["code"],
            )
        )
        data_agent = Agent(
            metadata=AgentMetadata(
                agent_id="data-agent",
                name="Data Agent",
                type=AgentType.EXECUTOR,
                domain="data",
                capabilities=["data"],
            )
        )

        code_agent.set_status(AgentStatus.READY)
        data_agent.set_status(AgentStatus.READY)

        registry.register_agent(sender)
        registry.register_agent(code_agent)
        registry.register_agent(data_agent)

        # Broadcast only to code domain
        responses = await router.broadcast_message(
            from_agent="sender",
            message_type=MessageType.BROADCAST,
            payload={"message": "code-only"},
            agent_filter=lambda a: a.metadata.domain == "code",
        )

        assert len(responses) == 1
        assert code_agent.messages_received == 1
        assert data_agent.messages_received == 0

    @pytest.mark.asyncio
    async def test_message_history(self) -> None:
        """Test message history tracking."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.messaging import MessageRouter, MessageType

        registry = AgentRegistry()
        router = MessageRouter(registry=registry)

        # Create agents
        agent1 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-1",
                name="Agent 1",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["test"],
            )
        )
        agent2 = Agent(
            metadata=AgentMetadata(
                agent_id="agent-2",
                name="Agent 2",
                type=AgentType.EXECUTOR,
                domain="general",
                capabilities=["test"],
            )
        )

        agent1.set_status(AgentStatus.READY)
        agent2.set_status(AgentStatus.READY)

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        # Send messages
        await router.send_message(
            from_agent="agent-1",
            to_agent="agent-2",
            message_type=MessageType.REQUEST,
            payload={"test": 1},
        )
        await router.send_message(
            from_agent="agent-2",
            to_agent="agent-1",
            message_type=MessageType.RESPONSE,
            payload={"test": 2},
        )

        # Check history
        history = router.get_message_history()
        assert len(history) == 2

        # Check filtered history
        agent1_history = router.get_message_history(agent_id="agent-1")
        assert len(agent1_history) == 2  # Both messages involve agent-1

        # Check statistics
        stats = router.get_statistics()
        assert stats["total_messages"] == 2


class TestPermissionSystem:
    """Tests for PermissionManager."""

    def test_permission_rule_creation(self) -> None:
        """Test creating permission rules."""
        from orchestrator._internal.agents.permissions import PermissionRule

        rule = PermissionRule(
            agent_id="agent-1", action="send_message", target="agent-2", allowed=True, priority=10
        )

        assert rule.agent_id == "agent-1"
        assert rule.action == "send_message"
        assert rule.target == "agent-2"
        assert rule.allowed is True
        assert rule.priority == 10

    def test_permission_rule_matching(self) -> None:
        """Test permission rule pattern matching."""
        from orchestrator._internal.agents.permissions import PermissionRule

        # Exact match
        rule = PermissionRule(
            agent_id="agent-1", action="send_message", target="agent-2", allowed=True
        )
        assert rule.matches("agent-1", "send_message", "agent-2") is True
        assert rule.matches("agent-1", "send_message", "agent-3") is False

        # Wildcard match
        wildcard_rule = PermissionRule(agent_id="agent-*", action="*", target="*", allowed=True)
        assert wildcard_rule.matches("agent-1", "send_message", "agent-2") is True
        assert wildcard_rule.matches("agent-99", "any_action", "any_target") is True

    def test_permission_manager_initialization(self) -> None:
        """Test permission manager initialization."""
        from orchestrator._internal.agents.permissions import PermissionManager

        manager = PermissionManager()
        assert len(manager) == 0

        stats = manager.get_statistics()
        assert stats["total_rules"] == 0
        assert stats["cached_checks"] == 0

    def test_add_and_check_permission(self) -> None:
        """Test adding rules and checking permissions."""
        from orchestrator._internal.agents.permissions import PermissionManager, PermissionRule

        manager = PermissionManager()

        # Add allow rule
        rule = PermissionRule(
            agent_id="agent-1", action="send_message", target="agent-2", allowed=True
        )
        manager.add_rule(rule)

        # Check permission
        assert manager.check_permission("agent-1", "send_message", "agent-2") is True
        assert manager.check_permission("agent-1", "send_message", "agent-3") is False

    def test_permission_priority(self) -> None:
        """Test permission rule priority."""
        from orchestrator._internal.agents.permissions import PermissionManager, PermissionRule

        manager = PermissionManager()

        # Add low priority deny rule
        deny_rule = PermissionRule(
            agent_id="agent-*", action="*", target="*", allowed=False, priority=0
        )
        manager.add_rule(deny_rule)

        # Add high priority allow rule
        allow_rule = PermissionRule(
            agent_id="agent-1", action="send_message", target="agent-2", allowed=True, priority=10
        )
        manager.add_rule(allow_rule)

        # High priority rule should take precedence
        assert manager.check_permission("agent-1", "send_message", "agent-2") is True
        # Low priority deny rule should apply to others
        assert manager.check_permission("agent-3", "send_message", "agent-4") is False

    def test_permission_cache(self) -> None:
        """Test permission check caching."""
        from orchestrator._internal.agents.permissions import PermissionManager, PermissionRule

        manager = PermissionManager()

        rule = PermissionRule(
            agent_id="agent-1", action="send_message", target="agent-2", allowed=True
        )
        manager.add_rule(rule)

        # First check (not cached)
        result1 = manager.check_permission("agent-1", "send_message", "agent-2", use_cache=True)

        # Second check (should use cache)
        result2 = manager.check_permission("agent-1", "send_message", "agent-2", use_cache=True)

        assert result1 == result2 is True

        stats = manager.get_statistics()
        assert stats["cached_checks"] >= 1


class TestLifecycleManagement:
    """Tests for AgentLifecycleManager."""

    @pytest.mark.asyncio
    async def test_lifecycle_manager_initialization(self) -> None:
        """Test lifecycle manager initialization."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        stats = lifecycle.get_statistics()
        assert stats["total_agents"] == 0
        assert stats["shutdown_hooks"] == 0

    @pytest.mark.asyncio
    async def test_initialize_agent(self) -> None:
        """Test agent initialization through lifecycle manager."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        metadata = AgentMetadata(
            agent_id="test-agent",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )

        agent = await lifecycle.initialize_agent(metadata, auto_register=True, set_ready=True)

        assert agent.metadata.agent_id == "test-agent"
        assert agent.status == AgentStatus.READY
        assert "test-agent" in registry

    @pytest.mark.asyncio
    async def test_shutdown_agent(self) -> None:
        """Test agent shutdown."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        # Initialize agent
        metadata = AgentMetadata(
            agent_id="test-agent",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        await lifecycle.initialize_agent(metadata)

        # Shutdown agent
        result = await lifecycle.shutdown_agent("test-agent", graceful=True)

        assert result is True
        assert "test-agent" not in registry

    @pytest.mark.asyncio
    async def test_shutdown_all_agents(self) -> None:
        """Test shutting down all agents."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        # Initialize multiple agents
        for i in range(3):
            metadata = AgentMetadata(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                type=AgentType.EXECUTOR,
                domain="testing",
                capabilities=["test"],
            )
            await lifecycle.initialize_agent(metadata)

        # Shutdown all
        results = await lifecycle.shutdown_all(graceful=True)

        assert len(results) == 3
        assert all(results.values())
        assert len(registry) == 0

    @pytest.mark.asyncio
    async def test_check_agent_health(self) -> None:
        """Test agent health checking."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        # Initialize agent
        metadata = AgentMetadata(
            agent_id="test-agent",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        await lifecycle.initialize_agent(metadata)

        # Check health
        health = lifecycle.check_agent_health("test-agent")

        assert health is not None
        assert health["agent_id"] == "test-agent"
        assert health["status"] == "ready"
        assert "uptime" in health

    @pytest.mark.asyncio
    async def test_shutdown_hooks(self) -> None:
        """Test shutdown hook execution."""
        from orchestrator._internal.agents.discovery import AgentRegistry
        from orchestrator._internal.agents.lifecycle import AgentLifecycleManager

        registry = AgentRegistry()
        lifecycle = AgentLifecycleManager(registry=registry)

        # Track hook execution
        hook_called = []

        def shutdown_hook() -> None:
            hook_called.append(True)

        lifecycle.register_shutdown_hook(shutdown_hook)

        # Initialize agent
        metadata = AgentMetadata(
            agent_id="test-agent",
            name="Test Agent",
            type=AgentType.EXECUTOR,
            domain="testing",
            capabilities=["test"],
        )
        await lifecycle.initialize_agent(metadata)

        # Shutdown all (should trigger hook)
        await lifecycle.shutdown_all()

        assert len(hook_called) == 1
