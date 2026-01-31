"""
Agent Management Skill

Wrapper around orchestrator._internal.agents module for creating
and managing agent instances.
"""

from typing import Any, Optional

try:
    from orchestrator._internal.agents import AgentRegistry

    _AgentRegistry: type | None = AgentRegistry
except ImportError:
    _AgentRegistry = None


class Skill:
    """
    Agent Management Skill following Agent Skills specification.

    Manages creation and lifecycle of agent instances.
    """

    def __init__(self) -> None:
        """Initialize agent management skill."""
        if _AgentRegistry:
            self._registry = _AgentRegistry()
        else:
            self._registry = None

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Main skill execution method."""
        return {"success": True, "message": "Agent management ready"}


# Global agent registry instance
_manager: Any = None


def get_manager() -> Any:
    """Get or create the global agent registry instance."""
    global _manager
    if _manager is None:
        if _AgentRegistry:
            _manager = _AgentRegistry()
    return _manager


def create_agent(
    name: str, agent_type: str = "default", config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Create a new agent instance."""
    manager = get_manager()

    if hasattr(manager, "create"):
        agent = manager.create(name=name, agent_type=agent_type, config=config or {})
        agent_id = agent.id if hasattr(agent, "id") else str(agent)
    else:
        agent_id = f"{name}_{agent_type}"

    return {"agent_id": agent_id, "name": name, "type": agent_type, "status": "created"}


def list_agents(status: str | None = None) -> list[dict[str, Any]]:
    """List all managed agents."""
    manager = get_manager()

    if hasattr(manager, "list_agents"):
        agents = manager.list_agents(status=status)
    else:
        agents = []

    return [
        {
            "agent_id": a.id if hasattr(a, "id") else str(a),
            "name": getattr(a, "name", "unknown"),
            "status": getattr(a, "status", "unknown"),
        }
        for a in agents
    ]


def get_agent_status(agent_id: str) -> dict[str, Any]:
    """Get current status of an agent."""
    manager = get_manager()

    if hasattr(manager, "get_status"):
        status = manager.get_status(agent_id)
    else:
        status = "unknown"

    return {"agent_id": agent_id, "status": status, "active": status == "active"}


def update_agent_config(agent_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """Update agent configuration."""
    manager = get_manager()

    if hasattr(manager, "update_config"):
        manager.update_config(agent_id, config)

    return {"agent_id": agent_id, "updated": True, "config": config}


def delete_agent(agent_id: str, force: bool = False) -> dict[str, Any]:
    """Remove/delete an agent."""
    manager = get_manager()

    if hasattr(manager, "delete"):
        manager.delete(agent_id, force=force)
        deleted = True
    else:
        deleted = False

    return {"agent_id": agent_id, "deleted": deleted, "force": force}


__all__ = ["create_agent", "list_agents", "get_agent_status", "update_agent_config", "delete_agent"]
