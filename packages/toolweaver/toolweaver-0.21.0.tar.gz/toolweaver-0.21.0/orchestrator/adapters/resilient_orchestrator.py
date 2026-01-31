"""
Resilient Orchestrator (Phase 7.1)

A wrapper that delegates to a primary backend but falls back to a backup
backend if the primary fails (e.g., LiteLLM proxy down, API rate limits).

Usage:
    from orchestrator.adapters.openai_native import OpenAINativeOrchestrator

    primary = ClaudeOrchestrator(config)
    backup = OpenAINativeOrchestrator(backup_config)

    orchestrator = ResilientOrchestrator(primary, backup)
    result = orchestrator.plan("do something")
"""

import logging
from typing import Any

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    PlanResult,
    ToolSchema,
)

logger = logging.getLogger(__name__)


class ResilientOrchestrator(OrchestratorBackend):
    """Fallback-enabled orchestrator wrapper."""

    def __init__(
        self,
        primary: OrchestratorBackend,
        backup: OrchestratorBackend,
    ):
        """
        Initialize resilient orchestrator.

        Args:
            primary: Main backend (e.g., Claude via LiteLLM)
            backup: Fallback backend (e.g., Native Azure)
        """
        # We use primary's config for base, though strictly not used by this wrapper
        super().__init__(primary.config)
        self.primary = primary
        self.backup = backup

    def register_tools(self, tools: list[ToolSchema]) -> None:
        """Register tools on both backends."""
        self.primary.register_tools(tools)
        self.backup.register_tools(tools)

    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """
        Try primary, fallback to backup on error.
        """
        try:
            return self.primary.plan(
                user_message, conversation_history, system_prompt
            )
        except Exception as e:
            logger.warning(
                f"Primary orchestrator failed: {e}. Falling back to backup."
            )
            # Tag fallback usage in logging/metrics could be added here

            # Sync history if needed?
            # OrchestratorBackend implementations usually maintain their own history
            # OR respect the passed `conversation_history`.
            # Since `conversation_history` is passed in, backup receives it.
            # But if primary had internal state (like ClaudeOrchestrator does),
            # and `conversation_history` passed here is None, we might lose
            # context accumulated in primary if we switch entirely.

            # However, `plan` is usually stateless per turn regarding the *current*
            # request, but stateful regarding history.

            # If we switch to backup for *this* turn, we should ensure backup
            # has the history.

            # Assuming `conversation_history` passed from outside is the source of truth
            # or we need to fetch it from primary?
            current_history = conversation_history
            if current_history is None:
                current_history = self.primary.get_conversation_history()

            return self.backup.plan(
                user_message, current_history, system_prompt
            )

    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        """Streaming fallback logic."""
        try:
            yield from self.primary.plan_streaming(
                user_message, conversation_history
            )
        except Exception as e:
            logger.warning(
                f"Primary streaming failed: {e}. Falling back to backup."
            )

            current_history = conversation_history
            if current_history is None:
                current_history = self.primary.get_conversation_history()

            yield from self.backup.plan_streaming(
                user_message, current_history
            )

    def add_tool_result(
        self,
        tool_call_id: str,
        result: str | dict[str, Any],
        is_error: bool = False,
    ) -> None:
        """Add result to both to keep them in sync."""
        self.primary.add_tool_result(tool_call_id, result, is_error)
        self.backup.add_tool_result(tool_call_id, result, is_error)

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get history (prefer primary)."""
        return self.primary.get_conversation_history()

    def clear_conversation_history(self) -> None:
        """Clear both."""
        self.primary.clear_conversation_history()
        self.backup.clear_conversation_history()
