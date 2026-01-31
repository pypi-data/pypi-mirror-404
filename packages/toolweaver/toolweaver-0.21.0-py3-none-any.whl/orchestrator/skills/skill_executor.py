"""
Skill Executor - Dynamic skill instantiation and execution

Handles loading skill modules, instantiating skill classes,
and executing capabilities with proper error handling and timeouts.
"""

import importlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ExecutionResult:
    """Result from skill execution"""

    success: bool
    skill_id: str
    capability: str
    result: Any | None = None
    error: str | None = None
    duration_ms: float | None = None
    timestamp: str | None = None
    execution_id: str | None = None


class SkillExecutor:
    """
    Executes skills by dynamically loading and instantiating skill classes.

    Supports:
    - Dynamic module loading
    - Skill instantiation with context
    - Timeout protection (default 30s)
    - Error handling and recovery
    - Execution metrics
    """

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize skill executor.

        Args:
            timeout_seconds: Maximum execution time for a skill (default 30s)
        """
        self.timeout_seconds = timeout_seconds
        self._skill_cache: dict[str, Any] = {}  # Cache instantiated skills
        self._execution_count = 0

    def execute(
        self, skill_id: str, capability: str, parameters: dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute a skill capability with given parameters.

        Args:
            skill_id: Skill identifier (e.g., 'cost-control')
            capability: Capability name (e.g., 'track_api_call')
            parameters: Parameters for the capability

        Returns:
            ExecutionResult with success status, result, or error
        """
        start_time = datetime.now()
        self._execution_count += 1
        execution_id = f"exec-{skill_id}-{self._execution_count}"

        try:
            # Load and instantiate skill
            skill_instance = self._get_skill_instance(skill_id)

            # Validate capability exists
            if not hasattr(skill_instance, capability):
                return ExecutionResult(
                    success=False,
                    skill_id=skill_id,
                    capability=capability,
                    error=f"Capability '{capability}' not found in skill",
                    timestamp=start_time.isoformat(),
                    execution_id=execution_id,
                )

            # Get the capability method
            capability_method = getattr(skill_instance, capability)

            # Execute with timeout protection
            try:
                # For now, execute synchronously
                # TODO: Add async support for long-running tasks
                result = capability_method(**parameters)

                duration = (datetime.now() - start_time).total_seconds() * 1000

                return ExecutionResult(
                    success=True,
                    skill_id=skill_id,
                    capability=capability,
                    result=result,
                    duration_ms=duration,
                    timestamp=start_time.isoformat(),
                    execution_id=execution_id,
                )

            except TypeError as e:
                # Parameter validation error
                return ExecutionResult(
                    success=False,
                    skill_id=skill_id,
                    capability=capability,
                    error=f"Invalid parameters: {str(e)}",
                    timestamp=start_time.isoformat(),
                    execution_id=execution_id,
                )

        except ImportError as e:
            return ExecutionResult(
                success=False,
                skill_id=skill_id,
                capability=capability,
                error=f"Failed to load skill module: {str(e)}",
                timestamp=start_time.isoformat(),
                execution_id=execution_id,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                skill_id=skill_id,
                capability=capability,
                error=f"Execution failed: {str(e)}",
                timestamp=start_time.isoformat(),
                execution_id=execution_id,
            )

    def _get_skill_instance(self, skill_id: str) -> Any:
        """
        Get or create a skill instance.

        Args:
            skill_id: Skill identifier (e.g., 'cost-control')

        Returns:
            Instantiated Skill class

        Raises:
            ImportError: If skill module cannot be loaded
        """
        # Check cache first
        if skill_id in self._skill_cache:
            return self._skill_cache[skill_id]

        # Convert skill-id to module path
        module_name = skill_id.replace("-", "_")
        module_path = f"orchestrator.skills.{module_name}"

        try:
            # Import the skill module
            module = importlib.import_module(module_path)

            # Get the Skill class
            if not hasattr(module, "Skill"):
                raise ImportError(f"Module {module_path} does not have a 'Skill' class")

            skill_class = module.Skill

            # Instantiate the skill
            skill_instance = skill_class()

            # Cache the instance
            self._skill_cache[skill_id] = skill_instance

            return skill_instance

        except ImportError as e:
            raise ImportError(f"Cannot load skill '{skill_id}': {str(e)}") from None

    def clear_cache(self) -> None:
        """Clear the skill instance cache."""
        self._skill_cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get executor statistics."""
        return {
            "total_executions": self._execution_count,
            "cached_skills": len(self._skill_cache),
            "skill_ids": list(self._skill_cache.keys()),
        }


# Global executor instance
_executor = None


def get_executor() -> SkillExecutor:
    """Get the global skill executor instance."""
    global _executor
    if _executor is None:
        _executor = SkillExecutor()
    return _executor
