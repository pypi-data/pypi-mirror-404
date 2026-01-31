"""
Dependency Resolution for ExecutionPlan.

Phase 0 Week 4 Day 2: Dependency Resolution

Resolves task dependencies into execution order using topological sorting,
handles conditional dependencies, and detects unresolvable conflicts.

Key responsibilities:
- Topological sort of dependency graph
- Circular dependency detection
- Missing dependency identification
- Resolution order generation
- Conflict detection
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .execution_plan import ExecutionPlan


class ResolutionStatus(Enum):
    """Status of dependency resolution."""

    RESOLVED = "resolved"
    CIRCULAR = "circular"
    MISSING = "missing"
    INVALID = "invalid"
    UNRESOLVED = "unresolved"


@dataclass
class ResolutionError:
    """Information about a resolution error."""

    status: ResolutionStatus
    step_ids: list[str]
    message: str
    affected_steps: list[str] | None = None

    def __post_init__(self) -> None:
        if self.affected_steps is None:
            self.affected_steps = []


class DependencyResolver:
    """
    Resolves task dependencies into execution order.

    Performs topological sorting of the dependency graph to determine
    execution order, detects cycles and missing dependencies, and
    validates the plan structure.
    """

    def __init__(self, plan: ExecutionPlan):
        """
        Initialize resolver for a plan.

        Args:
            plan: ExecutionPlan to resolve
        """
        self.plan = plan
        self.graph: dict[str, set[str]] = {}
        self.in_degree: dict[str, int] = {}
        self.errors: list[ResolutionError] = []
        self._build_graph()

    def _build_graph(self) -> None:
        """Build adjacency graph from plan."""
        # Initialize all steps
        for step in self.plan.steps:
            self.graph[step.id] = set()
            self.in_degree[step.id] = 0

        # Build edges from dependencies
        for step in self.plan.steps:
            for dep in step.depends_on:
                if dep in self.graph:
                    self.graph[dep].add(step.id)
                    self.in_degree[step.id] += 1

    def resolve(self) -> tuple[bool, list[str], list[ResolutionError]]:
        """
        Resolve plan dependencies into execution order.

        Returns:
            (success, execution_order, errors)
                - success: True if resolution was successful
                - execution_order: List of step IDs in execution order
                - errors: List of resolution errors (empty if successful)
        """
        self.errors = []

        # Handle empty plan
        if not self.plan.steps:
            return True, [], self.errors

        # Validate basic structure
        if not self._validate_structure():
            return False, [], self.errors

        # Detect circular dependencies
        if self._has_cycles():
            return False, [], self.errors

        # Perform topological sort
        order = self._topological_sort()
        if not order:
            self.errors.append(
                ResolutionError(
                    status=ResolutionStatus.UNRESOLVED,
                    step_ids=[s.id for s in self.plan.steps],
                    message="Unable to resolve execution order",
                )
            )
            return False, [], self.errors

        return True, order, self.errors

    def _validate_structure(self) -> bool:
        """Validate plan structure for basic issues."""
        missing_deps = []

        for step in self.plan.steps:
            for dep in step.depends_on:
                # Check for missing dependencies
                if not any(s.id == dep for s in self.plan.steps):
                    missing_deps.append(dep)

                # Check for self-dependency
                if dep == step.id:
                    self.errors.append(
                        ResolutionError(
                            status=ResolutionStatus.INVALID,
                            step_ids=[step.id],
                            message=f"Step {step.id} depends on itself",
                            affected_steps=[step.id],
                        )
                    )
                    return False

        if missing_deps:
            # Find which steps have missing dependencies
            affected = []
            for step in self.plan.steps:
                for dep in step.depends_on:
                    if not any(s.id == dep for s in self.plan.steps):
                        affected.append(step.id)
                        break

            self.errors.append(
                ResolutionError(
                    status=ResolutionStatus.MISSING,
                    step_ids=list(set(missing_deps)),
                    message=f"Missing dependencies: {', '.join(set(missing_deps))}",
                    affected_steps=affected,
                )
            )
            return False

        return True

    def _has_cycles(self) -> bool:
        """Detect cycles in dependency graph."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def visit(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    if visit(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    self.errors.append(
                        ResolutionError(
                            status=ResolutionStatus.CIRCULAR,
                            step_ids=cycle,
                            message=f"Circular dependency detected: {' -> '.join(cycle)}",
                            affected_steps=cycle[:-1],
                        )
                    )
                    return True

            rec_stack.discard(node)
            return False

        for step_id in self.graph:
            if step_id not in visited:
                if visit(step_id, []):
                    return True

        return False

    def _topological_sort(self) -> list[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of step IDs in topological order
        """
        if not self.graph:
            return []

        # Create working copy of in-degree
        in_degree = self.in_degree.copy()
        queue: list[str] = []

        # Find all nodes with in-degree 0
        for node, degree in in_degree.items():
            if degree == 0:
                queue.append(node)

        result = []

        while queue:
            # Sort for deterministic output
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for neighbors
            for neighbor in self.graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(result) != len(self.graph):
            return []

        return result

    def get_step_dependencies(self, step_id: str) -> list[str]:
        """
        Get direct dependencies for a step.

        Args:
            step_id: ID of the step

        Returns:
            List of step IDs this step depends on
        """
        for step in self.plan.steps:
            if step.id == step_id:
                return step.depends_on
        return []

    def get_step_dependents(self, step_id: str) -> list[str]:
        """
        Get steps that depend on this step.

        Args:
            step_id: ID of the step

        Returns:
            List of step IDs that depend on this step
        """
        return list(self.graph.get(step_id, set()))

    def get_transitive_dependencies(self, step_id: str) -> set[str]:
        """
        Get all transitive dependencies for a step.

        Args:
            step_id: ID of the step

        Returns:
            Set of all step IDs this step transitively depends on
        """
        deps = set()
        visited = set()

        def collect_deps(sid: str) -> None:
            if sid in visited:
                return
            visited.add(sid)

            for dep in self.get_step_dependencies(sid):
                deps.add(dep)
                collect_deps(dep)

        collect_deps(step_id)
        return deps

    def get_transitive_dependents(self, step_id: str) -> set[str]:
        """
        Get all steps that transitively depend on this step.

        Args:
            step_id: ID of the step

        Returns:
            Set of all step IDs that transitively depend on this step
        """
        dependents = set()
        visited = set()

        def collect_dependents(sid: str) -> None:
            if sid in visited:
                return
            visited.add(sid)

            for dep in self.get_step_dependents(sid):
                dependents.add(dep)
                collect_dependents(dep)

        collect_dependents(step_id)
        return dependents

    def can_execute_in_parallel(self, step_id_1: str, step_id_2: str) -> bool:
        """
        Check if two steps can execute in parallel.

        Args:
            step_id_1: First step ID
            step_id_2: Second step ID

        Returns:
            True if steps can execute in parallel (no dependency relationship)
        """
        deps_1 = self.get_transitive_dependencies(step_id_1)
        deps_2 = self.get_transitive_dependencies(step_id_2)

        # No parallel if one depends on the other
        if step_id_2 in deps_1 or step_id_1 in deps_2:
            return False

        return True

    def get_critical_path(self) -> list[str]:
        """
        Get critical path (longest dependency chain).

        Returns:
            List of step IDs forming the critical path
        """
        # Calculate longest path from each node to end
        memo: dict[str, tuple[int, list[str]]] = {}

        def longest_path(node: str) -> tuple[int, list[str]]:
            if node in memo:
                return memo[node]

            dependents = self.get_step_dependents(node)
            if not dependents:
                # Terminal node
                memo[node] = (1, [node])
                return memo[node]

            max_length = 0
            max_path = [node]

            for dependent in dependents:
                length, path = longest_path(dependent)
                if length + 1 > max_length:
                    max_length = length + 1
                    max_path = [node] + path

            memo[node] = (max_length, max_path)
            return memo[node]

        # Find starting nodes with no dependencies
        starts = [sid for sid, deps in self.in_degree.items() if deps == 0]

        if not starts:
            return []

        # Find longest path from starts
        max_length = 0
        critical = []

        for start in starts:
            length, path = longest_path(start)
            if length > max_length:
                max_length = length
                critical = path

        return critical

    def estimate_completion_time(self, durations: dict[str, float] | None = None) -> float:
        """
        Estimate total completion time considering parallelization.

        Args:
            durations: Optional dict mapping step_id to duration in seconds

        Returns:
            Estimated completion time in seconds
        """
        if not durations:
            durations = {}

        # Use critical path to estimate time
        critical = self.get_critical_path()
        total_time = 0.0

        for step_id in critical:
            duration = durations.get(step_id, 1.0)
            total_time += duration

        return total_time

    def get_resolution_stats(self) -> dict[str, Any]:
        """
        Get statistics about dependency resolution.

        Returns:
            Dictionary with resolution statistics
        """
        success, order, errors = self.resolve()

        stats = {
            "total_steps": len(self.plan.steps),
            "resolved": success,
            "execution_order_length": len(order) if success else 0,
            "error_count": len(errors),
            "error_types": {},
            "critical_path_length": len(self.get_critical_path()),
            "max_parallelization": self._calculate_max_parallelization(),
        }

        # Count errors by type
        error_types_dict: dict[str, int] = stats["error_types"]  # type: ignore[assignment]
        for error in errors:
            error_type = error.status.value
            error_types_dict[error_type] = error_types_dict.get(error_type, 0) + 1

        return stats

    def _calculate_max_parallelization(self) -> int:
        """Calculate maximum number of steps that can run in parallel."""
        if not self.plan.steps:
            return 0

        # Find widest level in dependency graph
        visited = set()
        max_width = 0

        def count_parallel(start_ids: set[str]) -> int:
            if not start_ids:
                return 0

            visited.update(start_ids)
            max_width_local = len(start_ids)

            # Find next level
            next_level = set()
            for sid in start_ids:
                for dependent in self.get_step_dependents(sid):
                    if dependent not in visited:
                        next_level.add(dependent)

            if next_level:
                max_width_local = max(max_width_local, count_parallel(next_level))

            return max_width_local

        # Start from nodes with no dependencies
        starts = {sid for sid, deps in self.in_degree.items() if deps == 0}
        max_width = count_parallel(starts)

        return max_width

    def get_level_groups(self) -> list[list[str]]:
        """
        Get steps grouped by dependency level.

        Returns:
            List of lists, where each inner list contains steps at same level
        """
        levels: list[list[str]] = []
        visited: set[str] = set()

        def get_level(start_ids: set[str]) -> None:
            if not start_ids or start_ids.issubset(visited):
                return

            current_level = []
            for sid in start_ids:
                if sid not in visited:
                    current_level.append(sid)
                    visited.add(sid)

            if current_level:
                levels.append(sorted(current_level))

            # Find next level
            next_level = set()
            for sid in current_level:
                for dependent in self.get_step_dependents(sid):
                    if dependent not in visited:
                        next_level.add(dependent)

            if next_level:
                get_level(next_level)

        # Start from nodes with no dependencies
        starts = {sid for sid, deps in self.in_degree.items() if deps == 0}
        get_level(starts)

        return levels
