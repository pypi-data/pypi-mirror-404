"""
Plan Execution Coordinator.

Phase 0 Week 4 Day 4: Integration

Coordinates execution of plans by distributing tasks across agents,
managing execution flow, handling errors, and tracking progress.

Integrates:
- ExecutionPlan (task structure)
- DependencyResolver (ordering)
- PlanOptimizer (optimization)
- Agent system (task execution)
- Orchestrator (overall coordination)
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from orchestrator._internal.infra.idempotency import (
    IdempotencyCache,
)
from orchestrator.context import ExecutionContext, get_execution_context, set_execution_context

from .dependency_resolver import DependencyResolver
from .execution_plan import ExecutionPlan, PlanStep, StepStatus
from .plan_optimizer import (
    OptimizationStrategy,
    PlanOptimizer,
)

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Mode of plan execution."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    OPTIMAL = "optimal"


class ExecutionPolicy(Enum):
    """Policy for handling step failures."""

    FAIL_FAST = "fail_fast"  # Stop on first failure
    CONTINUE = "continue"  # Continue with remaining steps
    SKIP_DEPENDENTS = "skip_dependents"  # Skip dependent steps


@dataclass
class StepExecution:
    """Execution result for a single step."""

    step_id: str
    status: StepStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration: float = 0.0
    retry_count: int = 0

    @property
    def is_success(self) -> bool:
        """Check if step executed successfully."""
        return self.status == StepStatus.COMPLETED

    @property
    def is_failure(self) -> bool:
        """Check if step failed."""
        return self.status == StepStatus.FAILED

    @property
    def is_done(self) -> bool:
        """Check if step is done (completed or failed)."""
        return self.status in (
            StepStatus.COMPLETED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
        )


@dataclass
class PlanExecutionResult:
    """Result of complete plan execution."""

    plan_id: str
    success: bool
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    start_time: datetime
    end_time: datetime
    step_results: dict[str, StepExecution] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Total execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Percentage of steps that succeeded."""
        if self.total_steps == 0:
            return 100.0
        return (self.completed_steps / self.total_steps) * 100


class StreamEventType(Enum):
    """Type of streaming event."""

    PLAN_STARTED = "plan_started"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"


@dataclass
class StreamEvent:
    """Event emitted during streaming execution."""

    event_type: StreamEventType
    timestamp: datetime
    plan_id: str
    step_id: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "data": self.data,
            "error": self.error,
        }


class PlanExecutor:
    """
    Executes ExecutionPlans with distributed task management.

    Coordinates step execution across agents, manages dependencies,
    handles failures, and provides progress tracking.
    """

    def __init__(
        self,
        plan: ExecutionPlan,
        mode: ExecutionMode = ExecutionMode.OPTIMAL,
        policy: ExecutionPolicy = ExecutionPolicy.SKIP_DEPENDENTS,
        session: ExecutionContext | None = None,
    ) -> None:
        """
        Initialize executor for a plan.

        Args:
            plan: ExecutionPlan to execute
            mode: Execution mode (sequential, parallel, optimal)
            policy: Failure handling policy
            session: Optional ExecutionContext for session tracking
        """
        self.plan = plan
        self.mode = mode
        self.policy = policy

        ctx = session or get_execution_context()
        if not ctx:
            ctx = ExecutionContext(task_description=f"Plan execution: {plan.id}")
        self.session: ExecutionContext = ctx

        self.resolver = DependencyResolver(plan)
        self.step_results: dict[str, StepExecution] = {}
        self.task_handlers: dict[str, Callable[..., Any]] = {}
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.idempotency_cache = IdempotencyCache(ttl_seconds=3600)

    def register_task_handler(self, agent_profile: str, handler: Callable[..., Any]) -> None:
        """
        Register handler for specific agent profile.

        Args:
            agent_profile: Agent profile name
            handler: Async callable that executes the task
        """
        self.task_handlers[agent_profile] = handler

    async def execute(self) -> PlanExecutionResult:
        """
        Execute the plan.

        Returns:
            PlanExecutionResult with execution details
        """
        self.start_time = datetime.now(timezone.utc)
        self.step_results = {}

        # Mark session as started if not already
        if self.session and self.session.status == "pending":
            self.session.mark_started()

        # Set as global context for nested skill execution
        old_context = get_execution_context()
        set_execution_context(self.session)

        try:
            # Resolve and validate plan
            success, order, errors = self.resolver.resolve()
            if not success:
                self.end_time = datetime.now(timezone.utc)
                if self.session:
                    self.session.mark_failed(
                        error=f"Plan resolution failed: {'; '.join(e.message for e in errors)}"
                    )
                return PlanExecutionResult(
                    plan_id=self.plan.id,
                    success=False,
                    total_steps=len(self.plan.steps),
                    completed_steps=0,
                    failed_steps=len(self.plan.steps),
                    skipped_steps=0,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    errors=[e.message for e in errors],
                )

            # Optimize plan if in optimal mode
            if self.mode == ExecutionMode.OPTIMAL:
                optimizer = PlanOptimizer(
                    self.plan,
                    strategy=OptimizationStrategy.MINIMIZE_EXECUTION_TIME,
                )
                opt_result = optimizer.optimize()
                if not opt_result.constraints_satisfied:
                    logger.warning(
                        "Optimization constraints not satisfied, proceeding with original plan"
                    )

            # Execute based on mode
            if self.mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(order)
            elif self.mode == ExecutionMode.PARALLEL:
                await self._execute_parallel()
            else:  # OPTIMAL
                await self._execute_optimal()

            # Compile results
            self.end_time = datetime.now(timezone.utc)
            result = self._compile_results()

            # Mark session as completed
            if result.success:
                if self.session:
                    self.session.mark_completed(result={"plan_execution": result.__dict__})
            else:
                if self.session:
                    self.session.mark_failed(
                        error=f"Plan execution failed: {result.failed_steps} steps failed"
                    )

            return result

        except Exception as e:
            self.end_time = datetime.now(timezone.utc)
            if self.session:
                self.session.mark_failed(error=str(e))
            raise

        finally:
            # Restore previous context
            if old_context:
                set_execution_context(old_context)
            else:
                # Clear if there was no previous context
                set_execution_context(None)

    async def execute_streaming(self) -> AsyncGenerator[StreamEvent, None]:
        """
        Execute plan and yield events as they occur.

        Yields StreamEvent objects for:
        - Plan start/completion/failure
        - Step start/completion/failure/skip

        Compatible with Server-Sent Events (SSE) and WebSocket.

        Yields:
            StreamEvent: Events during execution

        Example:
            async for event in executor.execute_streaming():
                if event.event_type == StreamEventType.STEP_COMPLETED:
                    print(f"Step {event.step_id} completed: {event.data}")
        """
        self.start_time = datetime.now(timezone.utc)
        self.step_results = {}

        # Mark session as started if not already
        if self.session.status == "pending":
            self.session.mark_started()

        # Set as global context
        old_context = get_execution_context()
        set_execution_context(self.session)

        # Emit plan started event
        yield StreamEvent(
            event_type=StreamEventType.PLAN_STARTED,
            timestamp=datetime.now(timezone.utc),
            plan_id=self.plan.id,
            data={
                "description": self.plan.description,
                "total_steps": len(self.plan.steps),
                "mode": self.mode.value,
            },
        )

        try:
            # Resolve and validate plan
            success, order, errors = self.resolver.resolve()
            if not success:
                error_msg = f"Plan resolution failed: {'; '.join(e.message for e in errors)}"
                self.end_time = datetime.now(timezone.utc)
                self.session.mark_failed(error=error_msg)

                yield StreamEvent(
                    event_type=StreamEventType.PLAN_FAILED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    error=error_msg,
                )
                return

            # Execute based on mode (sequential only for streaming)
            if self.mode == ExecutionMode.SEQUENTIAL:
                async for event in self._execute_sequential_streaming(order):
                    yield event
            else:
                # For parallel/optimal, fall back to sequential for streaming
                logger.warning(
                    f"Streaming not fully supported for {self.mode.value} mode, "
                    "falling back to sequential"
                )
                async for event in self._execute_sequential_streaming(order):
                    yield event

            # Compile results
            self.end_time = datetime.now(timezone.utc)
            result = self._compile_results()

            # Mark session appropriately
            if result.success:
                self.session.mark_completed(result={"plan_execution": result.__dict__})

                yield StreamEvent(
                    event_type=StreamEventType.PLAN_COMPLETED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    data={
                        "completed_steps": result.completed_steps,
                        "failed_steps": result.failed_steps,
                        "skipped_steps": result.skipped_steps,
                        "duration": result.duration,
                        "success_rate": result.success_rate,
                    },
                )
            else:
                error_msg = f"Plan execution failed: {result.failed_steps} steps failed"
                self.session.mark_failed(error=error_msg)

                yield StreamEvent(
                    event_type=StreamEventType.PLAN_FAILED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    error=error_msg,
                    data={
                        "completed_steps": result.completed_steps,
                        "failed_steps": result.failed_steps,
                        "errors": result.errors,
                    },
                )

        except Exception as e:
            self.end_time = datetime.now(timezone.utc)
            self.session.mark_failed(error=str(e))

            yield StreamEvent(
                event_type=StreamEventType.PLAN_FAILED,
                timestamp=datetime.now(timezone.utc),
                plan_id=self.plan.id,
                error=str(e),
            )

        finally:
            # Restore previous context
            if old_context:
                set_execution_context(old_context)
            else:
                set_execution_context(None)

    async def _execute_sequential_streaming(self, order: list[str]) -> AsyncGenerator[StreamEvent, None]:
        """Execute steps sequentially and yield events."""
        for step_id in order:
            if self._should_skip_step(step_id):
                self._mark_step_skipped(step_id)

                yield StreamEvent(
                    event_type=StreamEventType.STEP_SKIPPED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    step_id=step_id,
                )
                continue

            # Emit step started event
            step = self.plan.get_step(step_id)
            yield StreamEvent(
                event_type=StreamEventType.STEP_STARTED,
                timestamp=datetime.now(timezone.utc),
                plan_id=self.plan.id,
                step_id=step_id,
                data={
                    "task_description": step.task_description if step else None,
                    "agent_profile": step.agent_profile if step else None,
                },
            )

            # Execute step
            await self._execute_step(step_id)
            execution = self.step_results[step_id]

            # Emit result event
            if execution.is_failure:
                yield StreamEvent(
                    event_type=StreamEventType.STEP_FAILED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    step_id=step_id,
                    error=execution.error,
                    data={"duration": execution.duration},
                )

                if self.policy == ExecutionPolicy.FAIL_FAST:
                    break
                elif self.policy == ExecutionPolicy.SKIP_DEPENDENTS:
                    self._skip_dependents(step_id)
            else:
                yield StreamEvent(
                    event_type=StreamEventType.STEP_COMPLETED,
                    timestamp=datetime.now(timezone.utc),
                    plan_id=self.plan.id,
                    step_id=step_id,
                    data={
                        "result": execution.result,
                        "duration": execution.duration,
                    },
                )

    async def _execute_sequential(self, order: list[str]) -> None:
        """Execute steps sequentially."""
        for step_id in order:
            if self._should_skip_step(step_id):
                self._mark_step_skipped(step_id)
                continue

            await self._execute_step(step_id)

            if self.step_results[step_id].is_failure:
                if self.policy == ExecutionPolicy.FAIL_FAST:
                    break
                elif self.policy == ExecutionPolicy.SKIP_DEPENDENTS:
                    self._skip_dependents(step_id)

    async def _execute_parallel(self) -> None:
        """Execute steps in parallel following dependencies."""
        levels = self.resolver.get_level_groups()

        for level in levels:
            # Execute all steps in level in parallel
            tasks = []
            for step_id in level:
                if self._should_skip_step(step_id):
                    self._mark_step_skipped(step_id)
                else:
                    tasks.append(self._execute_step(step_id))

            if tasks:
                await asyncio.gather(*tasks)

            # Check for failures
            level_failures = [s for s in level if self.step_results[s].is_failure]
            if level_failures:
                if self.policy == ExecutionPolicy.FAIL_FAST:
                    break
                elif self.policy == ExecutionPolicy.SKIP_DEPENDENTS:
                    for failed_step in level_failures:
                        self._skip_dependents(failed_step)

    async def _execute_optimal(self) -> None:
        """Execute with optimal strategy (default to parallel)."""
        await self._execute_parallel()

    async def _execute_step(self, step_id: str) -> None:
        """Execute a single step."""
        step = self.plan.get_step(step_id)
        if not step:
            return

        execution = StepExecution(
            step_id=step_id,
            status=StepStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Check idempotency cache if session has idempotency_key
            if self.session and self.session.idempotency_key:
                cache_key = f"{self.session.idempotency_key}:{step_id}"
                cached_result = self.idempotency_cache.get(cache_key)

                if cached_result is not None:
                    # Return cached result
                    logger.info(f"Step {step_id} returned from idempotency cache")
                    self.plan.mark_step_completed(step_id, result=cached_result)
                    execution.status = StepStatus.COMPLETED
                    execution.result = cached_result
                    execution.ended_at = datetime.now(timezone.utc)
                    if execution.started_at:
                        execution.duration = (
                            execution.ended_at - execution.started_at
                        ).total_seconds()
                    self.step_results[step_id] = execution

                    # Track cache hit in session
                    if self.session:
                        self.session.add_metadata(
                            f"step_{step_id}_cached",
                            {
                                "step_id": step_id,
                                "cache_hit": True,
                                "duration_seconds": execution.duration,
                            },
                        )
                    return

            # Get handler for this step's agent profile
            handler = self.task_handlers.get(step.agent_profile, self._default_handler)

            # Execute step
            self.plan.mark_step_started(step_id)

            # Track step in session metadata
            if self.session and execution.started_at:
                self.session.add_metadata(
                    f"step_{step_id}_started",
                    {
                        "step_id": step_id,
                        "agent_profile": step.agent_profile,
                        "started_at": execution.started_at.isoformat(),
                    },
                )

            result = await handler(step)

            # Store in idempotency cache if session has idempotency_key
            if self.session and self.session.idempotency_key:
                cache_key = f"{self.session.idempotency_key}:{step_id}"
                self.idempotency_cache.store(cache_key, result, status="success")

            # Mark as completed
            self.plan.mark_step_completed(step_id, result=result)
            execution.status = StepStatus.COMPLETED
            execution.result = result

            # Track completion in session
            if self.session:
                self.session.add_metadata(
                    f"step_{step_id}_completed",
                    {
                        "step_id": step_id,
                        "duration_seconds": execution.duration,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                    },
                )

            logger.info(f"Step {step_id} completed successfully")

        except Exception as e:
            # Mark as failed
            error_msg = str(e)
            self.plan.mark_step_failed(step_id, error=error_msg)
            execution.status = StepStatus.FAILED
            execution.error = error_msg

            # Track failure in session
            if self.session:
                self.session.add_metadata(
                    f"step_{step_id}_failed",
                    {
                        "step_id": step_id,
                        "error": error_msg,
                    },
                )

            logger.error(f"Step {step_id} failed: {error_msg}")

        finally:
            execution.ended_at = datetime.now(timezone.utc)
            if execution.started_at:
                execution.duration = (execution.ended_at - execution.started_at).total_seconds()
            self.step_results[step_id] = execution

    async def _default_handler(self, step: PlanStep) -> dict[str, Any]:
        """Default handler for steps without registered handler."""
        logger.info(f"Executing {step.id} with default handler (profile: {step.agent_profile})")
        return {
            "status": "executed",
            "step_id": step.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _should_skip_step(self, step_id: str) -> bool:
        """Check if step should be skipped."""
        # Skip if dependencies failed
        deps = self.resolver.get_step_dependencies(step_id)
        for dep_id in deps:
            if dep_id in self.step_results:
                if self.step_results[dep_id].is_failure:
                    if self.policy == ExecutionPolicy.SKIP_DEPENDENTS:
                        return True
        return False

    def _mark_step_skipped(self, step_id: str) -> None:
        """Mark a step as skipped."""
        step = self.plan.get_step(step_id)
        if step:
            step.status = StepStatus.SKIPPED
            self.step_results[step_id] = StepExecution(
                step_id=step_id,
                status=StepStatus.SKIPPED,
            )

    def _skip_dependents(self, step_id: str) -> None:
        """Skip all steps dependent on given step."""
        dependents = self.resolver.get_transitive_dependents(step_id)
        for dep_id in dependents:
            if dep_id not in self.step_results:
                self._mark_step_skipped(dep_id)

    def _compile_results(self) -> PlanExecutionResult:
        """Compile execution results."""
        completed = sum(1 for r in self.step_results.values() if r.status == StepStatus.COMPLETED)
        failed = sum(1 for r in self.step_results.values() if r.status == StepStatus.FAILED)
        skipped = sum(1 for r in self.step_results.values() if r.status == StepStatus.SKIPPED)

        # Ensure start_time and end_time are not None
        start_time_val = self.start_time if self.start_time else datetime.now(timezone.utc)
        end_time_val = self.end_time if self.end_time else datetime.now(timezone.utc)

        return PlanExecutionResult(
            plan_id=self.plan.id,
            success=failed == 0,
            total_steps=len(self.plan.steps),
            completed_steps=completed,
            failed_steps=failed,
            skipped_steps=skipped,
            start_time=start_time_val,
            end_time=end_time_val,
            step_results=self.step_results,
        )

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of execution."""
        if not self.end_time or not self.start_time:
            return {"status": "not_executed"}

        return {
            "plan_id": self.plan.id,
            "mode": self.mode.value,
            "policy": self.policy.value,
            "duration": (self.end_time - self.start_time).total_seconds(),
            "total_steps": len(self.plan.steps),
            "completed": sum(
                1 for r in self.step_results.values() if r.status == StepStatus.COMPLETED
            ),
            "failed": sum(1 for r in self.step_results.values() if r.status == StepStatus.FAILED),
            "skipped": sum(1 for r in self.step_results.values() if r.status == StepStatus.SKIPPED),
            "step_results": {
                step_id: {
                    "status": result.status.value,
                    "duration": result.duration,
                    "error": result.error,
                }
                for step_id, result in self.step_results.items()
            },
        }
