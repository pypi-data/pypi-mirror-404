"""
Plan Optimization for ExecutionPlan.

Phase 0 Week 4 Day 3: Plan Optimization

Optimizes execution plans based on resources, priorities, and constraints
to maximize parallelization and minimize total execution time.

Key responsibilities:
- Resource-aware scheduling
- Priority-based step reordering
- Parallel group optimization
- Constraint handling (time limits, resource quotas)
- Execution time estimation with resource contention
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .dependency_resolver import DependencyResolver
from .execution_plan import ExecutionPlan


class OptimizationStrategy(Enum):
    """Strategy for plan optimization."""

    MAXIMIZE_PARALLELIZATION = "maximize_parallelization"
    MINIMIZE_EXECUTION_TIME = "minimize_execution_time"
    MINIMIZE_RESOURCE_USAGE = "minimize_resource_usage"
    BALANCED = "balanced"


class ResourceType(Enum):
    """Type of resource constraint."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CUSTOM = "custom"


@dataclass
class ResourceRequirement:
    """Resource requirement for a step."""

    resource_type: ResourceType
    amount: float
    unit: str = "units"


@dataclass
class ResourcePool:
    """Available resources for execution."""

    resource_type: ResourceType
    total_available: float
    currently_used: float = 0.0

    @property
    def available(self) -> float:
        """Get currently available resources."""
        return self.total_available - self.currently_used


@dataclass
class OptimizationConstraint:
    """Constraint for plan optimization."""

    constraint_type: str  # "max_parallel", "max_duration", "min_gap", etc.
    target: str  # step_id or "plan"
    value: float
    enabled: bool = True


@dataclass
class OptimizationResult:
    """Result of plan optimization."""

    optimized_plan: ExecutionPlan
    strategy_used: OptimizationStrategy
    improvement_percent: float
    estimated_duration: float
    max_parallelization: int
    constraints_satisfied: bool
    issues: list[str] = field(default_factory=list)


class PlanOptimizer:
    """
    Optimizes ExecutionPlan for efficient parallel execution.

    Applies optimization strategies considering resource constraints,
    priorities, and execution time to create efficient execution schedules.
    """

    def __init__(
        self,
        plan: ExecutionPlan,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
    ):
        """
        Initialize optimizer.

        Args:
            plan: ExecutionPlan to optimize
            strategy: Optimization strategy to use
        """
        self.plan = plan
        self.strategy = strategy
        self.resolver = DependencyResolver(plan)
        self.constraints: list[OptimizationConstraint] = []
        self.resource_pools: dict[ResourceType, ResourcePool] = {}
        self.resource_requirements: dict[str, list[ResourceRequirement]] = {}
        self.step_durations: dict[str, float] = {}
        self.step_priorities: dict[str, int] = {}

    def add_resource_pool(self, resource_type: ResourceType, total_available: float) -> None:
        """
        Add resource pool for optimization.

        Args:
            resource_type: Type of resource
            total_available: Total available amount
        """
        self.resource_pools[resource_type] = ResourcePool(
            resource_type=resource_type, total_available=total_available
        )

    def set_resource_requirement(self, step_id: str, requirement: ResourceRequirement) -> None:
        """
        Set resource requirement for a step.

        Args:
            step_id: ID of the step
            requirement: ResourceRequirement
        """
        if step_id not in self.resource_requirements:
            self.resource_requirements[step_id] = []
        self.resource_requirements[step_id].append(requirement)

    def set_step_duration(self, step_id: str, duration: float) -> None:
        """
        Set estimated duration for a step.

        Args:
            step_id: ID of the step
            duration: Duration in seconds
        """
        self.step_durations[step_id] = duration

    def set_step_priority(self, step_id: str, priority: int) -> None:
        """
        Set priority for a step (higher = more important).

        Args:
            step_id: ID of the step
            priority: Priority value (0-100)
        """
        self.step_priorities[step_id] = max(0, min(100, priority))

    def add_constraint(self, constraint: OptimizationConstraint) -> None:
        """
        Add optimization constraint.

        Args:
            constraint: OptimizationConstraint to add
        """
        self.constraints.append(constraint)

    def optimize(self) -> OptimizationResult:
        """
        Optimize the plan.

        Returns:
            OptimizationResult with optimized plan and metrics
        """
        # Resolve dependencies
        success, order, errors = self.resolver.resolve()
        if not success:
            return OptimizationResult(
                optimized_plan=self.plan,
                strategy_used=self.strategy,
                improvement_percent=0.0,
                estimated_duration=0.0,
                max_parallelization=0,
                constraints_satisfied=False,
                issues=[e.message for e in errors],
            )

        # Get level groups for analysis
        levels = self.resolver.get_level_groups()

        # Apply optimization based on strategy
        if self.strategy == OptimizationStrategy.MAXIMIZE_PARALLELIZATION:
            optimized = self._optimize_parallelization(levels)
        elif self.strategy == OptimizationStrategy.MINIMIZE_EXECUTION_TIME:
            optimized = self._optimize_execution_time(levels)
        elif self.strategy == OptimizationStrategy.MINIMIZE_RESOURCE_USAGE:
            optimized = self._optimize_resources(levels)
        else:  # BALANCED
            optimized = self._optimize_balanced(levels)

        # Calculate metrics
        baseline_duration = self.resolver.estimate_completion_time(self.step_durations)
        optimized_duration = self._estimate_duration(optimized)
        improvement = (
            (baseline_duration - optimized_duration) / baseline_duration * 100
            if baseline_duration > 0
            else 0
        )

        constraints_satisfied = self._check_constraints(optimized)

        return OptimizationResult(
            optimized_plan=optimized,
            strategy_used=self.strategy,
            improvement_percent=max(0, improvement),
            estimated_duration=optimized_duration,
            max_parallelization=len(
                self.resolver.get_level_groups()[0] if self.resolver.get_level_groups() else []
            ),
            constraints_satisfied=constraints_satisfied,
        )

    def _optimize_parallelization(self, levels: list[list[str]]) -> ExecutionPlan:
        """Optimize for maximum parallelization."""
        optimized = ExecutionPlan(
            id=self.plan.id + "-optimized",
            description=self.plan.description + " (parallelization optimized)",
        )

        # Copy steps
        for step in self.plan.steps:
            optimized.add_step(step)

        # Reorder within levels to maintain parallelization
        for level in levels:
            # Sort by priority (descending)
            level.sort(
                key=lambda s: self.step_priorities.get(s, 50),
                reverse=True,
            )

        return optimized

    def _optimize_execution_time(self, levels: list[list[str]]) -> ExecutionPlan:
        """Optimize for minimum execution time."""
        optimized = ExecutionPlan(
            id=self.plan.id + "-optimized",
            description=self.plan.description + " (time optimized)",
        )

        # Copy steps
        for step in self.plan.steps:
            optimized.add_step(step)

        # Within each level, prioritize by duration (longest first)
        # This helps complete critical paths faster
        for level in levels:
            level.sort(
                key=lambda s: self.step_durations.get(s, 1.0),
                reverse=True,
            )

        return optimized

    def _optimize_resources(self, levels: list[list[str]]) -> ExecutionPlan:
        """Optimize for minimum resource usage."""
        optimized = ExecutionPlan(
            id=self.plan.id + "-optimized",
            description=self.plan.description + " (resource optimized)",
        )

        # Copy steps
        for step in self.plan.steps:
            optimized.add_step(step)

        # Within levels, prioritize by resource usage (lowest first)
        for level in levels:
            level.sort(
                key=lambda s: sum(req.amount for req in self.resource_requirements.get(s, [])),
                reverse=False,
            )

        return optimized

    def _optimize_balanced(self, levels: list[list[str]]) -> ExecutionPlan:
        """Balanced optimization strategy."""
        # Combine multiple objectives
        optimized = ExecutionPlan(
            id=self.plan.id + "-optimized",
            description=self.plan.description + " (balanced optimized)",
        )

        # Copy steps
        for step in self.plan.steps:
            optimized.add_step(step)

        # Score each step and sort within levels
        def score_step(step_id: str) -> float:
            """Calculate composite score for step."""
            priority_score = self.step_priorities.get(step_id, 50) / 100.0
            duration_score = min(1.0, self.step_durations.get(step_id, 1.0) / 10.0)
            resource_score = min(
                1.0,
                sum(req.amount for req in self.resource_requirements.get(step_id, [])) / 100.0,
            )

            return priority_score * 0.5 + duration_score * 0.3 - resource_score * 0.2

        for level in levels:
            level.sort(key=score_step, reverse=True)

        return optimized

    def _estimate_duration(self, plan: ExecutionPlan) -> float:
        """Estimate execution duration for optimized plan."""
        if not plan.steps:
            return 0.0

        resolver = DependencyResolver(plan)
        levels = resolver.get_level_groups()

        total_duration = 0.0

        for level in levels:
            # Parallel steps take max time, not sum
            level_duration = max(self.step_durations.get(step_id, 1.0) for step_id in level)
            total_duration += level_duration

        return total_duration

    def _check_constraints(self, plan: ExecutionPlan) -> bool:
        """Check if optimized plan satisfies constraints."""
        if not self.constraints:
            return True

        for constraint in self.constraints:
            if not constraint.enabled:
                continue

            if constraint.constraint_type == "max_parallel":
                # Check max parallel steps
                levels = DependencyResolver(plan).get_level_groups()
                max_parallel = max(len(level) for level in levels) if levels else 0
                if max_parallel > constraint.value:
                    return False

            elif constraint.constraint_type == "max_duration":
                # Check total execution time
                duration = self._estimate_duration(plan)
                if duration > constraint.value:
                    return False

        return True

    def get_optimization_report(self) -> dict[str, Any]:
        """Get detailed optimization report."""
        report: dict[str, Any] = {
            "strategy": self.strategy.value,
            "total_steps": len(self.plan.steps),
            "levels": len(self.resolver.get_level_groups()),
            "critical_path_length": len(self.resolver.get_critical_path()),
            "max_possible_parallelization": self.resolver._calculate_max_parallelization(),
            "baseline_duration": self.resolver.estimate_completion_time(self.step_durations),
            "constraints_count": len(self.constraints),
            "resource_pools": {
                rt.value: {
                    "total": rp.total_available,
                    "used": rp.currently_used,
                    "available": rp.available,
                }
                for rt, rp in self.resource_pools.items()
            },
        }
        return report

    def get_step_schedule(self, plan: ExecutionPlan) -> dict[str, dict[str, Any]]:
        """
        Get execution schedule for steps.

        Returns:
            Dict mapping step_id to schedule info (timing, resources, etc.)
        """
        resolver = DependencyResolver(plan)
        levels = resolver.get_level_groups()

        schedule = {}
        current_time = 0.0

        for level_idx, level in enumerate(levels):
            level_start_time = current_time
            max_level_duration = 0.0

            for step_id in level:
                step_duration = self.step_durations.get(step_id, 1.0)
                schedule[step_id] = {
                    "level": level_idx,
                    "start_time": level_start_time,
                    "end_time": level_start_time + step_duration,
                    "duration": step_duration,
                    "resources": [
                        {
                            "type": req.resource_type.value,
                            "amount": req.amount,
                            "unit": req.unit,
                        }
                        for req in self.resource_requirements.get(step_id, [])
                    ],
                }
                max_level_duration = max(max_level_duration, step_duration)

            current_time = level_start_time + max_level_duration

        return schedule

    def get_parallelization_matrix(self) -> dict[str, list[str]]:
        """
        Get matrix of which steps can execute in parallel.

        Returns:
            Dict mapping step_id to list of step_ids that can run in parallel
        """
        matrix = {}
        for step in self.plan.steps:
            parallel_steps = []
            for other_step in self.plan.steps:
                if step.id != other_step.id and self.resolver.can_execute_in_parallel(
                    step.id, other_step.id
                ):
                    parallel_steps.append(other_step.id)
            matrix[step.id] = parallel_steps
        return matrix

    def recommend_strategy(self) -> OptimizationStrategy:
        """
        Recommend best strategy based on plan characteristics.

        Returns:
            Recommended OptimizationStrategy
        """
        stats = self.resolver.get_resolution_stats()

        # Calculate characteristics
        total_steps = stats["total_steps"]
        max_parallel = stats.get("max_parallelization", 1)
        critical_path = stats["critical_path_length"]

        # If high parallelization potential, maximize it
        if max_parallel > total_steps * 0.5:
            return OptimizationStrategy.MAXIMIZE_PARALLELIZATION

        # If resource constraints exist
        if self.resource_pools:
            return OptimizationStrategy.MINIMIZE_RESOURCE_USAGE

        # If tight execution time requirements
        if critical_path > total_steps * 0.7:
            return OptimizationStrategy.MINIMIZE_EXECUTION_TIME

        # Default to balanced
        return OptimizationStrategy.BALANCED
