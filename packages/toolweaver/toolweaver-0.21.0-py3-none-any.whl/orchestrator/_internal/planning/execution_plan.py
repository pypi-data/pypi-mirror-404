"""
Execution Plan - Structured plan for agent-based task execution.

Phase 0 Week 4: Planning System
Day 1: ExecutionPlan Structure

Defines the core data structures for representing execution plans that enable
parallel task execution through dependency tracking and step organization.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StepStatus(Enum):
    """Status of a plan step during execution."""

    PENDING = "pending"  # Waiting to execute
    READY = "ready"  # Dependencies satisfied, can execute
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Execution failed
    SKIPPED = "skipped"  # Skipped (condition not met)


class PlanStatus(Enum):
    """Status of entire execution plan."""

    CREATED = "created"  # Just created
    READY = "ready"  # Ready to execute
    EXECUTING = "executing"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Plan execution failed
    PARTIAL = "partial"  # Partially completed (some steps failed)


@dataclass
class PlanStep:
    """
    Individual step in an execution plan.

    Represents a single task with its requirements, dependencies,
    and execution constraints.
    """

    id: str  # Unique identifier (auto-generated if not provided)
    task_description: str  # What this step does
    agent_profile: str  # Which agent profile should handle this (e.g., "developer", "researcher")

    # Execution constraints
    depends_on: list[str] = field(default_factory=list)  # Step IDs this depends on
    can_be_parallel: bool = True  # Can this run in parallel with other steps?

    # Capabilities and requirements
    required_capabilities: list[str] = field(default_factory=list)  # Capabilities needed

    # Execution metadata
    status: StepStatus = StepStatus.PENDING
    priority: int = 0  # Higher = more important (for scheduling)
    estimated_duration: float | None = None  # Estimated seconds
    timeout: float | None = None  # Max seconds to allow

    # Results and tracking
    result: dict[str, Any] | None = None  # Step result
    error: str | None = None  # Error message if failed
    start_time: datetime | None = None
    end_time: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize id if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def duration(self) -> float | None:
        """Get actual execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_ready(self) -> bool:
        """Check if this step is ready to execute (all dependencies complete)."""
        return self.status == StepStatus.READY

    @property
    def is_done(self) -> bool:
        """Check if step has finished (success or failure)."""
        return self.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)

    def to_dict(self) -> dict[str, Any]:
        """Serialize step to dictionary."""
        return {
            "id": self.id,
            "task_description": self.task_description,
            "agent_profile": self.agent_profile,
            "depends_on": list(self.depends_on),
            "can_be_parallel": self.can_be_parallel,
            "required_capabilities": list(self.required_capabilities),
            "status": self.status.value,
            "priority": self.priority,
            "estimated_duration": self.estimated_duration,
            "timeout": self.timeout,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanStep":
        """Deserialize step from dictionary."""
        start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None

        return cls(
            id=data.get("id") or "",
            task_description=data["task_description"],
            agent_profile=data["agent_profile"],
            depends_on=data.get("depends_on", []) or [],
            can_be_parallel=data.get("can_be_parallel", True),
            required_capabilities=data.get("required_capabilities", []) or [],
            status=StepStatus(data.get("status", StepStatus.PENDING.value)),
            priority=data.get("priority", 0),
            estimated_duration=data.get("estimated_duration"),
            timeout=data.get("timeout"),
            result=data.get("result"),
            error=data.get("error"),
            start_time=start_time,
            end_time=end_time,
        )


@dataclass
class ExecutionPlan:
    """
    Complete execution plan with structured task dependency graph.

    Enables parallel execution by tracking dependencies and identifying
    steps that can run concurrently.
    """

    id: str  # Unique plan identifier
    description: str  # What this plan accomplishes
    steps: list[PlanStep] = field(default_factory=list)  # All steps in order

    # Dependency tracking
    dependencies: dict[str, list[str]] = field(default_factory=dict)  # step_id -> [depends_on_ids]

    # Metadata
    status: PlanStatus = PlanStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize dependencies from steps if not provided."""
        if not self.dependencies and self.steps:
            self.dependencies = {step.id: step.depends_on for step in self.steps}

    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
        self.dependencies[step.id] = step.depends_on

    def get_step(self, step_id: str) -> PlanStep | None:
        """Get step by ID."""
        return next((s for s in self.steps if s.id == step_id), None)

    def get_dependency_levels(self) -> list[list[str]]:
        """
        Group steps by dependency level for parallel execution.

        Returns list of lists where each inner list contains step IDs
        that can run in parallel (have no mutual dependencies).

        Example:
            [[step1, step2], [step3, step4], [step5]]
            - step1 and step2 can run in parallel
            - step3 and step4 can run in parallel (after steps 1,2)
            - step5 runs after steps 3,4
        """
        levels: list[list[str]] = []
        assigned: set[str] = set()

        # Keep finding levels until all steps assigned
        while len(assigned) < len(self.steps):
            current_level: list[str] = []

            for step in self.steps:
                if step.id in assigned:
                    continue

                # Check if all dependencies are already assigned
                deps = self.dependencies.get(step.id, [])
                if all(dep_id in assigned for dep_id in deps):
                    current_level.append(step.id)

            if not current_level:
                # No progress - circular dependency or error
                break

            levels.append(current_level)
            assigned.update(current_level)

        return levels

    def get_ready_steps(self) -> list[str]:
        """Get list of step IDs that are ready to execute."""
        completed: set[str] = {step.id for step in self.steps if step.is_done}

        ready: list[str] = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps = self.dependencies.get(step.id, [])
            if all(dep_id in completed for dep_id in deps):
                ready.append(step.id)

        return ready

    def get_parallel_groups(self) -> list[list[PlanStep]]:
        """
        Get steps grouped for parallel execution.

        Returns list of step groups that can execute in parallel.
        """
        levels = self.get_dependency_levels()
        return [
            [step for step_id in level if (step := self.get_step(step_id)) is not None]
            for level in levels
        ]

    def mark_step_ready(self, step_id: str) -> bool:
        """Mark a step as ready to execute."""
        step = self.get_step(step_id)
        if step and step.status == StepStatus.PENDING:
            # Verify dependencies are complete
            deps = self.dependencies.get(step_id, [])
            for dep_step in self.steps:
                if dep_step.id in deps and not dep_step.is_done:
                    return False

            step.status = StepStatus.READY
            return True
        return False

    def mark_step_started(self, step_id: str) -> bool:
        """Mark a step as started."""
        step = self.get_step(step_id)
        if step and step.status == StepStatus.READY:
            step.status = StepStatus.RUNNING
            step.start_time = datetime.now()
            return True
        return False

    def mark_step_completed(self, step_id: str, result: dict[str, Any] | None = None) -> bool:
        """Mark a step as completed with optional result."""
        step = self.get_step(step_id)
        if step and step.status == StepStatus.RUNNING:
            step.status = StepStatus.COMPLETED
            step.result = result
            step.end_time = datetime.now()
            return True
        return False

    def mark_step_failed(self, step_id: str, error: str) -> bool:
        """Mark a step as failed with error message."""
        step = self.get_step(step_id)
        if step and step.status in (StepStatus.PENDING, StepStatus.READY, StepStatus.RUNNING):
            step.status = StepStatus.FAILED
            step.error = error
            step.end_time = datetime.now()
            return True
        return False

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the plan for correctness.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Check for missing steps in dependencies
        all_step_ids = {step.id for step in self.steps}
        for step_id, deps in self.dependencies.items():
            if step_id not in all_step_ids:
                errors.append(f"Dependency references unknown step: {step_id}")
            for dep_id in deps:
                if dep_id not in all_step_ids:
                    errors.append(f"Step {step_id} depends on unknown step: {dep_id}")

        # Check for circular dependencies
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.dependencies.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for step_id in self.dependencies:
            if step_id not in visited:
                if has_cycle(step_id):
                    errors.append(f"Circular dependency detected involving {step_id}")
                    break

        return len(errors) == 0, errors

    def get_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        total_steps = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        running = sum(1 for s in self.steps if s.status == StepStatus.RUNNING)

        total_duration: float = 0
        for step in self.steps:
            if step.duration:
                total_duration += step.duration

        return {
            "total_steps": total_steps,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total_steps - completed - failed - running,
            "total_duration": total_duration,
            "status": self.status.value,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize execution plan to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPlan":
        """Deserialize execution plan from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        completed_at = (
            datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )

        steps = [PlanStep.from_dict(s) for s in data.get("steps", [])]
        plan = cls(
            id=data["id"],
            description=data.get("description", ""),
            steps=steps,
            dependencies=data.get("dependencies", {}),
            status=PlanStatus(data.get("status", PlanStatus.CREATED.value)),
            created_at=created_at or datetime.now(),
            started_at=started_at,
            completed_at=completed_at,
        )
        return plan

    def to_json(self) -> str:
        """Serialize execution plan to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        """Deserialize execution plan from JSON string."""
        return cls.from_dict(json.loads(json_str))
