"""
Workflow System for Tool Composition (Phase 8)

Enables automatic tool chaining, dependency management, and context sharing
for complex multi-tool workflows.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a workflow step execution"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    SUSPENDED = "suspended"


@dataclass
class ActionRequirement:
    """Requirement for user action to proceed"""

    action_type: str  # e.g., "approval", "input"
    description: str
    step_id: str
    schema: dict[str, Any] | None = None  # Expected input schema for "input" type


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Features:
    - Tool name reference
    - Parameter templates with variable substitution
    - Dependency tracking
    - Conditional execution
    - Retry configuration
    """

    step_id: str
    tool_name: str
    parameters: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None  # e.g., "{{step1.success}} == true"
    requires_approval: bool = False
    retry_count: int = 0
    timeout_seconds: int | None = None

    def __post_init__(self) -> None:
        """Validate step configuration"""
        if not self.step_id:
            raise ValueError("step_id is required")
        if not self.tool_name:
            raise ValueError("tool_name is required")
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create WorkflowStep from dictionary"""
        return cls(
            step_id=data["step_id"],
            tool_name=data["tool_name"],
            parameters=data["parameters"],
            depends_on=data.get("depends_on", []),
            condition=data.get("condition"),
            requires_approval=data.get("requires_approval", False),
            retry_count=data.get("retry_count", 0),
            timeout_seconds=data.get("timeout_seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert WorkflowStep to dictionary"""
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "requires_approval": self.requires_approval,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class WorkflowTemplate:
    """
    A reusable workflow template with multiple steps.

    Example:
        github_pr_workflow = WorkflowTemplate(
            name="github_pr_workflow",
            description="Create PR and notify team",
            steps=[
                WorkflowStep(
                    step_id="list_issues",
                    tool_name="github_list_issues",
                    parameters={"repo": "{{repo}}"}
                ),
                WorkflowStep(
                    step_id="create_pr",
                    tool_name="github_create_pr",
                    depends_on=["list_issues"],
                    parameters={
                        "repo": "{{repo}}",
                        "title": "{{pr_title}}"
                    }
                )
            ]
        )
    """

    name: str
    description: str
    steps: list[WorkflowStep]
    metadata: dict[str, Any] = field(default_factory=dict)
    parallel_groups: list[list[str]] | None = None

    def __post_init__(self) -> None:
        """Validate workflow configuration"""
        if not self.name:
            raise ValueError("name is required")
        if not self.steps:
            raise ValueError("workflow must have at least one step")

        # Validate unique step IDs
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_ids must be unique")

        # Validate dependencies exist
        valid_ids = set(step_ids)
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in valid_ids:
                    raise ValueError(f"Step '{step.step_id}' depends on non-existent step '{dep}'")

    def get_step(self, step_id: str) -> WorkflowStep | None:
        """Get step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowTemplate":
        """Create WorkflowTemplate from dictionary"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[WorkflowStep.from_dict(s) for s in data["steps"]],
            metadata=data.get("metadata", {}),
            parallel_groups=data.get("parallel_groups"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert WorkflowTemplate to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
            "parallel_groups": self.parallel_groups,
        }


class WorkflowContext:
    """
    Shared context for workflow execution.

    Features:
    - Store step results
    - Share data between steps
    - Variable substitution
    - Type-safe data access
    """

    def __init__(self, initial_variables: dict[str, Any] | None = None):
        self.step_results: dict[str, Any] = {}
        self.step_status: dict[str, StepStatus] = {}
        self.variables: dict[str, Any] = initial_variables or {}
        self.errors: dict[str, Exception] = {}
        self.suspension: ActionRequirement | None = None

    def set_suspended(self, requirement: ActionRequirement) -> None:
        """Mark workflow as suspended requiring action"""
        self.suspension = requirement
        self.step_status[requirement.step_id] = StepStatus.SUSPENDED

    def set_result(
        self, step_id: str, result: Any, status: StepStatus = StepStatus.SUCCESS
    ) -> None:
        """Store result from a step execution"""
        self.step_results[step_id] = result
        self.step_status[step_id] = status

    def set_error(self, step_id: str, error: Exception) -> None:
        """Store error from a failed step"""
        self.errors[step_id] = error
        self.step_status[step_id] = StepStatus.FAILED

    def get_result(self, step_id: str) -> Any:
        """Retrieve result from a previous step"""
        return self.step_results.get(step_id)

    def get_status(self, step_id: str) -> StepStatus | None:
        """Get status of a step"""
        return self.step_status.get(step_id)

    def is_success(self, step_id: str) -> bool:
        """Check if a step completed successfully"""
        return self.step_status.get(step_id) == StepStatus.SUCCESS

    def substitute(self, template: Any) -> Any:
        """
        Substitute variables in template.

        Supports:
        - {{variable}} - Direct variable substitution
        - {{step_id.field}} - Access step result fields
        - {{step_id.field.nested}} - Nested field access

        Args:
            template: String template or dict with templates

        Returns:
            Substituted value (same type as input)
        """
        if isinstance(template, str):
            return self._substitute_string(template)
        elif isinstance(template, dict):
            return {k: self.substitute(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.substitute(item) for item in template]
        else:
            return template

    def _substitute_string(self, template: str) -> str:
        """Substitute variables in a string template"""
        pattern = r"\{\{([^}]+)\}\}"

        def replacer(match: Any) -> str:
            expression = match.group(1).strip()
            try:
                value = self._evaluate_expression(expression)
                return str(value) if value is not None else ""
            except Exception as e:
                logger.warning(f"Failed to substitute '{expression}': {e}")
                return str(match.group(0))  # Return original if substitution fails

        return re.sub(pattern, replacer, template)

    def _evaluate_expression(self, expression: str) -> Any:
        """
        Evaluate a variable expression.

        Examples:
            "repo" -> self.variables["repo"]
            "step1.result" -> self.step_results["step1"]["result"]
            "step1.user.email" -> self.step_results["step1"]["user"]["email"]
        """
        # Check for direct variable first
        if expression in self.variables:
            return self.variables[expression]

        # Check for step result access (step_id.field.nested)
        if "." in expression:
            parts = expression.split(".")
            step_id = parts[0]

            if step_id in self.step_results:
                value = self.step_results[step_id]

                # Navigate nested fields
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        return None

                return value

        return None

    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary"""
        suspension_dict = None
        if self.suspension:
            suspension_dict = {
                "action_type": self.suspension.action_type,
                "description": self.suspension.description,
                "step_id": self.suspension.step_id,
                "schema": self.suspension.schema,
            }

        return {
            "step_results": self.step_results,
            "step_status": {k: v.value for k, v in self.step_status.items()},
            "variables": self.variables,
            "errors": {k: str(v) for k, v in self.errors.items()},
            "suspension": suspension_dict,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowContext":
        """Reconstruct context from dictionary"""
        context = cls(initial_variables=data.get("variables"))
        context.step_results = data.get("step_results", {})

        # Restore status enum
        status_map = data.get("step_status", {})
        for step_id, status_str in status_map.items():
            try:
                context.step_status[step_id] = StepStatus(status_str)
            except ValueError:
                logger.warning(f"Unknown status '{status_str}' for step '{step_id}'")

        # Restore errors (note: original exceptions are lost, stored as strings)
        error_map = data.get("errors", {})
        for step_id, error_msg in error_map.items():
            context.errors[step_id] = Exception(error_msg)

        # Restore suspension
        susp_data = data.get("suspension")
        if susp_data:
            context.suspension = ActionRequirement(
                action_type=susp_data["action_type"],
                description=susp_data["description"],
                step_id=susp_data["step_id"],
                schema=susp_data.get("schema")
            )

        return context
