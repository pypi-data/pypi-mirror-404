"""
Agent Discovery System

Provides agent registration, discovery, and search capabilities.
Integrates with ProfileLoader to load agent profiles from YAML files.

Components:
- AgentRegistry: Central registry for agent registration and discovery
- Profile-based discovery: Load agents from YAML profiles
- Search capabilities: Find agents by type, capability, domain, tools

Design:
- Registry maintains in-memory index of all agents
- Supports dynamic registration/deregistration
- Provides multiple search methods for flexible discovery
- Integrates with ProfileLoader for profile-based agent creation

Usage:
    registry = AgentRegistry(profile_loader=loader)

    # Register an agent
    registry.register_agent(agent)

    # Load agent from profile
    agent = registry.load_agent_from_profile("researcher")

    # Search agents
    executors = registry.find_agents_by_type(AgentType.EXECUTOR)
    search_agents = registry.find_agents_by_capability("search")
    code_agents = registry.find_agents_by_domain("code")
"""

import logging
from typing import Any

from ..backends.profiles.base import ProfileLoader
from .agent import Agent, AgentMetadata, AgentStatus, AgentType

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Exception raised for agent registry errors."""

    pass


class AgentRegistry:
    """
    Central registry for agent discovery and management.

    Maintains an in-memory index of all registered agents and provides
    search capabilities by type, capability, domain, and tools.

    Attributes:
        _agents: Dictionary mapping agent_id to Agent instances
        _by_type: Index of agents by type
        _by_capability: Index of agents by capability
        _by_domain: Index of agents by domain
        _by_tool: Index of agents by tool
        profile_loader: Optional ProfileLoader for loading agent profiles
    """

    def __init__(self, profile_loader: ProfileLoader | None = None) -> None:
        """
        Initialize agent registry.

        Args:
            profile_loader: Optional ProfileLoader for loading agent profiles from files
        """
        self._agents: dict[str, Agent] = {}
        self._by_type: dict[AgentType, set[str]] = {t: set() for t in AgentType}
        self._by_capability: dict[str, set[str]] = {}
        self._by_domain: dict[str, set[str]] = {}
        self._by_tool: dict[str, set[str]] = {}
        self.profile_loader = profile_loader

        logger.info("Initialized AgentRegistry")

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent in the registry.

        Args:
            agent: Agent instance to register

        Raises:
            RegistryError: If agent_id already registered
        """
        agent_id = agent.metadata.agent_id

        if agent_id in self._agents:
            raise RegistryError(f"Agent already registered: {agent_id}")

        # Add to main registry
        self._agents[agent_id] = agent

        # Index by type
        self._by_type[agent.metadata.type].add(agent_id)

        # Index by capabilities
        for capability in agent.metadata.capabilities:
            if capability not in self._by_capability:
                self._by_capability[capability] = set()
            self._by_capability[capability].add(agent_id)

        # Index by domain
        domain = agent.metadata.domain
        if domain not in self._by_domain:
            self._by_domain[domain] = set()
        self._by_domain[domain].add(agent_id)

        # Index by tools
        for tool in agent.metadata.tools:
            if tool not in self._by_tool:
                self._by_tool[tool] = set()
            self._by_tool[tool].add(agent_id)

        logger.info(
            f"Registered agent: {agent_id} (type={agent.metadata.type.value}, domain={domain})"
        )

    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the registry.

        Args:
            agent_id: ID of agent to deregister

        Returns:
            True if agent was deregistered, False if not found
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent not found for deregistration: {agent_id}")
            return False

        agent = self._agents[agent_id]

        # Remove from type index
        self._by_type[agent.metadata.type].discard(agent_id)

        # Remove from capability index
        for capability in agent.metadata.capabilities:
            if capability in self._by_capability:
                self._by_capability[capability].discard(agent_id)
                if not self._by_capability[capability]:
                    del self._by_capability[capability]

        # Remove from domain index
        domain = agent.metadata.domain
        if domain in self._by_domain:
            self._by_domain[domain].discard(agent_id)
            if not self._by_domain[domain]:
                del self._by_domain[domain]

        # Remove from tool index
        for tool in agent.metadata.tools:
            if tool in self._by_tool:
                self._by_tool[tool].discard(agent_id)
                if not self._by_tool[tool]:
                    del self._by_tool[tool]

        # Remove from main registry
        del self._agents[agent_id]

        logger.info(f"Deregistered agent: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Agent | None:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID to lookup

        Returns:
            Agent instance if found, None otherwise
        """
        return self._agents.get(agent_id)

    def list_agents(self) -> list[Agent]:
        """
        List all registered agents.

        Returns:
            List of all Agent instances
        """
        return list(self._agents.values())

    def find_agents_by_type(self, agent_type: AgentType) -> list[Agent]:
        """
        Find all agents of a specific type.

        Args:
            agent_type: AgentType to search for

        Returns:
            List of Agent instances matching the type
        """
        agent_ids = self._by_type.get(agent_type, set())
        return [self._agents[aid] for aid in agent_ids]

    def find_agents_by_capability(self, capability: str) -> list[Agent]:
        """
        Find all agents with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of Agent instances with the capability
        """
        agent_ids = self._by_capability.get(capability, set())
        return [self._agents[aid] for aid in agent_ids]

    def find_agents_by_domain(self, domain: str) -> list[Agent]:
        """
        Find all agents in a specific domain.

        Args:
            domain: Domain to search for

        Returns:
            List of Agent instances in the domain
        """
        agent_ids = self._by_domain.get(domain, set())
        return [self._agents[aid] for aid in agent_ids]

    def find_agents_by_tool(self, tool: str) -> list[Agent]:
        """
        Find all agents that have a specific tool.

        Args:
            tool: Tool name to search for

        Returns:
            List of Agent instances with the tool
        """
        agent_ids = self._by_tool.get(tool, set())
        return [self._agents[aid] for aid in agent_ids]

    def find_agents(
        self,
        agent_type: AgentType | None = None,
        capability: str | None = None,
        domain: str | None = None,
        tool: str | None = None,
        status: AgentStatus | None = None,
    ) -> list[Agent]:
        """
        Find agents matching multiple criteria (AND logic).

        Args:
            agent_type: Optional type filter
            capability: Optional capability filter
            domain: Optional domain filter
            tool: Optional tool filter
            status: Optional status filter

        Returns:
            List of Agent instances matching all specified criteria
        """
        # Start with all agents
        result_ids = set(self._agents.keys())

        # Apply type filter
        if agent_type is not None:
            result_ids &= self._by_type.get(agent_type, set())

        # Apply capability filter
        if capability is not None:
            result_ids &= self._by_capability.get(capability, set())

        # Apply domain filter
        if domain is not None:
            result_ids &= self._by_domain.get(domain, set())

        # Apply tool filter
        if tool is not None:
            result_ids &= self._by_tool.get(tool, set())

        # Get agents and apply status filter if needed
        agents = [self._agents[aid] for aid in result_ids]

        if status is not None:
            agents = [a for a in agents if a.status == status]

        return agents

    def load_agent_from_profile(
        self, profile_name: str, agent_id: str | None = None, auto_register: bool = True
    ) -> Agent:
        """
        Load an agent from a profile file.

        Args:
            profile_name: Name of profile to load (without .yaml extension)
            agent_id: Optional custom agent ID (defaults to profile_name)
            auto_register: Whether to automatically register the agent

        Returns:
            Agent instance created from profile

        Raises:
            RegistryError: If profile_loader not configured or profile invalid
        """
        if self.profile_loader is None:
            raise RegistryError("No profile loader configured")

        try:
            # Load profile
            profile = self.profile_loader.load_profile(profile_name)

            # Extract agent metadata from profile
            agent_id = agent_id or profile_name
            name = profile.get("name", profile_name)
            agent_type_str = profile.get("type", "executor")
            domain = profile.get("domain", "general")
            capabilities = profile.get("capabilities", [])
            tools = profile.get("tools", [])
            description = profile.get("description", "")
            metadata = profile.get("metadata", {})

            # Parse agent type
            try:
                agent_type = AgentType(agent_type_str.lower())
            except ValueError:
                logger.warning(f"Invalid agent type '{agent_type_str}', defaulting to EXECUTOR")
                agent_type = AgentType.EXECUTOR

            # Create agent metadata
            agent_metadata = AgentMetadata(
                agent_id=agent_id,
                name=name,
                type=agent_type,
                domain=domain,
                capabilities=capabilities,
                tools=tools,
                description=description,
                metadata=metadata,
            )

            # Create agent
            agent = Agent(metadata=agent_metadata)

            # Auto-register if requested
            if auto_register:
                self.register_agent(agent)

            logger.info(f"Loaded agent from profile: {profile_name} -> {agent_id}")
            return agent

        except Exception as e:
            raise RegistryError(
                f"Failed to load agent from profile '{profile_name}': {e}"
            ) from None

    def load_agents_from_directory(self, auto_register: bool = True) -> list[Agent]:
        """
        Load all agents from profile directory.

        Args:
            auto_register: Whether to automatically register all agents

        Returns:
            List of Agent instances created from profiles

        Raises:
            RegistryError: If profile_loader not configured
        """
        if self.profile_loader is None:
            raise RegistryError("No profile loader configured")

        agents = []
        profile_names = self.profile_loader.list_profiles()

        for profile_name in profile_names:
            try:
                agent = self.load_agent_from_profile(profile_name, auto_register=auto_register)
                agents.append(agent)
            except RegistryError as e:
                logger.error(f"Failed to load profile '{profile_name}': {e}")
                continue

        logger.info(f"Loaded {len(agents)} agents from directory")
        return agents

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_agents": len(self._agents),
            "by_type": {t.value: len(ids) for t, ids in self._by_type.items() if ids},
            "by_status": self._count_by_status(),
            "capabilities": len(self._by_capability),
            "domains": len(self._by_domain),
            "tools": len(self._by_tool),
        }

    def _count_by_status(self) -> dict[str, int]:
        """Count agents by status."""
        counts: dict[str, int] = {}
        for agent in self._agents.values():
            status_value = agent.status.value
            counts[status_value] = counts.get(status_value, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear all agents from registry."""
        count = len(self._agents)
        self._agents.clear()
        for agent_set in self._by_type.values():
            agent_set.clear()
        self._by_capability.clear()
        self._by_domain.clear()
        self._by_tool.clear()
        logger.info(f"Cleared registry ({count} agents removed)")

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if agent_id is registered."""
        return agent_id in self._agents

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={len(self._agents)}, domains={len(self._by_domain)})"
