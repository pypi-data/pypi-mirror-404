"""
Permission System for Agent Communication

Provides permission-based access control for agent interactions.
Integrates with AuthProvider for extensible authentication.

Components:
- PermissionRule: Defines permission rules for agent actions
- PermissionManager: Manages and enforces permission rules

Design:
- Rule-based permission system with wildcard matching
- Integrates with AuthProvider for authentication checks
- Supports agent-to-agent and agent-to-resource permissions
- Flexible rule matching with pattern support

Usage:
    manager = PermissionManager(auth_provider=auth)

    # Add permission rule
    rule = PermissionRule(
        agent_id="agent-1",
        action="send_message",
        target="agent-2",
        allowed=True
    )
    manager.add_rule(rule)

    # Check permission
    if manager.check_permission("agent-1", "send_message", "agent-2"):
        # Allow action
        pass
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, cast

from ..backends.auth.base import AuthProvider

logger = logging.getLogger(__name__)


@dataclass
class PermissionRule:
    """
    Defines a permission rule for agent actions.

    Attributes:
        agent_id: Agent ID or pattern (supports wildcards with *)
        action: Action type (e.g., "send_message", "read_state")
        target: Target agent ID or pattern (supports wildcards with *)
        allowed: Whether the action is allowed
        priority: Rule priority (higher values take precedence)
        metadata: Additional rule metadata
    """

    agent_id: str
    action: str
    target: str
    allowed: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def matches(self, agent_id: str, action: str, target: str) -> bool:
        """
        Check if this rule matches the given parameters.

        Args:
            agent_id: Agent ID to check
            action: Action to check
            target: Target to check

        Returns:
            True if rule matches all parameters
        """
        return (
            self._pattern_match(self.agent_id, agent_id)
            and self._pattern_match(self.action, action)
            and self._pattern_match(self.target, target)
        )

    def _pattern_match(self, pattern: str, value: str) -> bool:
        """
        Match value against pattern (supports * wildcard).

        Args:
            pattern: Pattern to match (may contain *)
            value: Value to check

        Returns:
            True if value matches pattern
        """
        if pattern == "*":
            return True
        if "*" in pattern:
            # Convert wildcard pattern to regex
            regex_pattern = pattern.replace("*", ".*")
            return re.match(f"^{regex_pattern}$", value) is not None
        return pattern == value


class PermissionManager:
    """
    Manages and enforces permission rules for agent actions.

    Provides centralized permission checking with rule-based access control.
    Supports wildcard patterns and priority-based rule resolution.

    Attributes:
        auth_provider: Optional AuthProvider for authentication integration
        _rules: List of permission rules
        _rule_cache: Cache for permission check results
    """

    def __init__(self, auth_provider: AuthProvider | None = None):
        """
        Initialize permission manager.

        Args:
            auth_provider: Optional AuthProvider for authentication integration
        """
        self.auth_provider = auth_provider
        self._rules: list[PermissionRule] = []
        self._rule_cache: dict[str, bool] = {}

        logger.info("Initialized PermissionManager")

    def add_rule(self, rule: PermissionRule) -> None:
        """
        Add a permission rule.

        Args:
            rule: PermissionRule to add
        """
        self._rules.append(rule)
        # Sort rules by priority (highest first)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        # Clear cache when rules change
        self._rule_cache.clear()
        logger.debug(
            f"Added permission rule: {rule.agent_id} -> {rule.action} -> {rule.target} (allowed={rule.allowed})"
        )

    def remove_rule(self, rule: PermissionRule) -> bool:
        """
        Remove a permission rule.

        Args:
            rule: PermissionRule to remove

        Returns:
            True if rule was removed, False if not found
        """
        try:
            self._rules.remove(rule)
            self._rule_cache.clear()
            logger.debug(
                f"Removed permission rule: {rule.agent_id} -> {rule.action} -> {rule.target}"
            )
            return True
        except ValueError:
            return False

    def check_permission(
        self, agent_id: str, action: str, target: str, use_cache: bool = True
    ) -> bool:
        """
        Check if an agent has permission to perform an action on a target.

        Args:
            agent_id: Agent ID requesting permission
            action: Action to perform
            target: Target of the action
            use_cache: Whether to use cached results

        Returns:
            True if permission is granted, False otherwise
        """
        # Check cache
        cache_key = f"{agent_id}:{action}:{target}"
        if use_cache and cache_key in self._rule_cache:
            return self._rule_cache[cache_key]

        # Check with AuthProvider if available
        if self.auth_provider:
            try:
                # AuthProvider may have its own permission logic
                if hasattr(self.auth_provider, "check_permission"):
                    result = self.auth_provider.check_permission(agent_id, action, target)
                    if result is not None and isinstance(result, bool):
                        self._rule_cache[cache_key] = result
                        return cast(bool, result)
            except Exception as e:
                logger.warning(f"AuthProvider check failed: {e}")

        # Check rules (highest priority first)
        for rule in self._rules:
            if rule.matches(agent_id, action, target):
                self._rule_cache[cache_key] = rule.allowed
                logger.debug(
                    f"Permission check: {agent_id} -> {action} -> {target} = {rule.allowed}"
                )
                return rule.allowed

        # Default: deny if no matching rule found
        self._rule_cache[cache_key] = False
        logger.debug(
            f"Permission check: {agent_id} -> {action} -> {target} = False (no matching rule)"
        )
        return False

    def get_rules(
        self, agent_id: str | None = None, action: str | None = None, target: str | None = None
    ) -> list[PermissionRule]:
        """
        Get all rules matching the given filters.

        Args:
            agent_id: Optional agent ID filter
            action: Optional action filter
            target: Optional target filter

        Returns:
            List of matching PermissionRule instances
        """
        rules = self._rules

        if agent_id:
            rules = [r for r in rules if r.agent_id == agent_id or r.agent_id == "*"]

        if action:
            rules = [r for r in rules if r.action == action or r.action == "*"]

        if target:
            rules = [r for r in rules if r.target == target or r.target == "*"]

        return rules

    def clear_rules(self, agent_id: str | None = None) -> int:
        """
        Clear all rules, or rules for a specific agent.

        Args:
            agent_id: Optional agent ID to clear rules for

        Returns:
            Number of rules cleared
        """
        if agent_id:
            before = len(self._rules)
            self._rules = [r for r in self._rules if r.agent_id != agent_id]
            cleared = before - len(self._rules)
        else:
            cleared = len(self._rules)
            self._rules.clear()

        self._rule_cache.clear()
        logger.info(f"Cleared {cleared} permission rules")
        return cleared

    def clear_cache(self) -> None:
        """Clear the permission check cache."""
        count = len(self._rule_cache)
        self._rule_cache.clear()
        logger.debug(f"Cleared {count} cached permission checks")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get permission system statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_rules": len(self._rules),
            "cached_checks": len(self._rule_cache),
            "has_auth_provider": self.auth_provider is not None,
        }

    def __len__(self) -> int:
        """Return number of rules."""
        return len(self._rules)

    def __repr__(self) -> str:
        return f"PermissionManager(rules={len(self._rules)}, cached={len(self._rule_cache)})"
