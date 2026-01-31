"""
Workflow Execution Engine (Phase 8.1, 8.2 & 8.3)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any

from .workflow import ActionRequirement, StepStatus, WorkflowContext, WorkflowStep, WorkflowTemplate

logger = logging.getLogger(__name__)


class StepDecision(Enum):
    """Decision for step execution"""
    RUN = "run"
    SKIP = "skip"
    WAIT = "wait"
    SUSPEND = "suspend"
    ALREADY_DONE = "already_done"


class WorkflowExecutor:
    """
    Execute workflows with dependency resolution and parallel execution.

    Features:
    - Topological sort for dependency resolution
    - Parallel execution of independent steps
    - Error handling with retries
    - Context management
    - Human-in-the-loop suspension (Phase 8.2)
    - Persistence and Resumption (Phase 8.3)
    """

    def __init__(self, tool_executor: Any | None = None, state_store: Any | None = None):
        """
        Initialize workflow executor.

        Args:
            tool_executor: Executor for running tools (execute method).
            state_store: Persistence store for workflow state (save_state, load_state).
        """
        self.tool_executor = tool_executor
        self.state_store = state_store

    async def execute(
        self,
        workflow: WorkflowTemplate,
        initial_variables: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        context: WorkflowContext | None = None,
    ) -> WorkflowContext:
        """
        Start a new workflow execution.

        Args:
            workflow: Workflow template
            initial_variables: Start variables (ignored if context provided)
            workflow_id: Optional ID for persistence
            context: Optional existing context
        """
        if context is None:
            context = WorkflowContext(initial_variables)

        return await self._run_workflow_loop(workflow, context, workflow_id)

    async def resume(
        self,
        workflow: WorkflowTemplate,
        workflow_id: str,
        additional_variables: dict[str, Any] | None = None
    ) -> WorkflowContext:
        """
        Resume a suspended workflow.

        Args:
            workflow: Workflow template (must match original)
            workflow_id: ID of the stored state
            additional_variables: Variables to merge (e.g. approvals, inputs)
        """
        if not self.state_store:
            raise ValueError("State store not configured")

        context = self.state_store.load_state(workflow_id)
        if not context:
            raise ValueError(f"No state found for workflow ID: {workflow_id}")

        # clear previous suspension
        context.suspension = None

        # Merge new variables (e.g. approvals)
        if additional_variables:
            context.variables.update(additional_variables)

        logger.info(f"Resuming workflow '{workflow_id}'")
        return await self._run_workflow_loop(workflow, context, workflow_id)

    async def _run_workflow_loop(
        self,
        workflow: WorkflowTemplate,
        context: WorkflowContext,
        workflow_id: str | None
    ) -> WorkflowContext:
        """Internal execution loop"""
        # Save initial state
        if workflow_id and self.state_store:
            self.state_store.save_state(workflow_id, context)

        logger.info(f"Executing workflow: {workflow.name}")
        start_time = time.time()

        try:
            levels = self._resolve_dependencies(workflow.steps)
            logger.info(f"Workflow has {len(levels)} execution levels")

            for _level_num, level_steps in enumerate(levels):
                # If we are suspended, stop BEFORE processing next level?
                # Actually if we just resumed, we want to continue.
                # If we get suspended IN this level, we break.

                executable_steps = []
                for step in level_steps:
                    decision = self._evaluate_step_decision(step, context)

                    if decision == StepDecision.RUN:
                        executable_steps.append(step)
                    elif decision == StepDecision.SKIP:
                        # Only mark skipped if not already processed?
                        # If it was already skipped, do nothing.
                        if context.get_status(step.step_id) != StepStatus.SKIPPED:
                            context.set_result(step.step_id, None, StepStatus.SKIPPED)
                            logger.info(f"Skipping step '{step.step_id}'")
                    elif decision == StepDecision.SUSPEND:
                        req = ActionRequirement(
                            action_type="approval",
                            description=f"Approval required for step '{step.step_id}'",
                            step_id=step.step_id
                        )
                        context.set_suspended(req)
                        logger.info(f"Suspending step '{step.step_id}' for approval")
                    elif decision == StepDecision.WAIT:
                        logger.debug(f"Step '{step.step_id}' waiting for dependencies")
                    elif decision == StepDecision.ALREADY_DONE:
                        logger.debug(f"Step '{step.step_id}' already completed")

                # If suspended, break loop
                if context.suspension:
                    logger.info("Workflow suspended.")
                    break

                if not executable_steps:
                    continue

                # Execute steps in parallel
                tasks = [self._execute_step(step, context) for step in executable_steps]
                await asyncio.gather(*tasks, return_exceptions=False)

                # Check for fatal errors if we wanted to stop on error?
                # For now continue.

            duration = time.time() - start_time
            logger.info(f"Workflow execution finished in {duration:.2f}s")

            # Save state if ID provided
            if workflow_id and self.state_store:
                self.state_store.save_state(workflow_id, context)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            # Try to save state even on failure?
            if workflow_id and self.state_store:
                try:
                    self.state_store.save_state(workflow_id, context)
                except Exception as se:
                    logger.error(f"Failed to save state during error handling: {se}")
            raise

        return context

    def _resolve_dependencies(self, steps: list[WorkflowStep]) -> list[list[WorkflowStep]]:
        """Resolve dependencies using topological sort."""
        step_map = {step.step_id: step for step in steps}
        current_in_degree = {step.step_id: len(step.depends_on) for step in steps}

        levels = []
        processed_count = 0
        total_steps = len(steps)

        while processed_count < total_steps:
            current_level_ids = [
                sid for sid, degree in current_in_degree.items()
                if degree == 0
            ]

            if not current_level_ids:
                 remaining_ids = list(current_in_degree.keys())
                 raise ValueError(
                    f"Circular dependency detected in workflow. Remaining steps: {remaining_ids}"
                )

            current_level_steps = [step_map[sid] for sid in current_level_ids]
            levels.append(current_level_steps)

            for sid in current_level_ids:
                del current_in_degree[sid]
                processed_count += 1

            for remaining_sid in current_in_degree:
                step = step_map[remaining_sid]
                for dep in step.depends_on:
                    if dep in current_level_ids:
                        current_in_degree[remaining_sid] -= 1

        return levels

    def _evaluate_step_decision(self, step: WorkflowStep, context: WorkflowContext) -> StepDecision:
        """Determine what to do with a step."""
        # 0. Check if already done
        current_status = context.get_status(step.step_id)
        if current_status in (StepStatus.SUCCESS, StepStatus.SKIPPED, StepStatus.FAILED):
            return StepDecision.ALREADY_DONE

        # 1. Check dependencies
        for dep in step.depends_on:
            status = context.get_status(dep)
            if status == StepStatus.SUCCESS:
                continue
            elif status in (StepStatus.FAILED, StepStatus.SKIPPED):
                return StepDecision.SKIP
            else:
                # Dependency not ready (PENDING, RUNNING, SUSPENDED)
                # If dependency is SUSPENDED, we wait.
                return StepDecision.WAIT

        # 2. Check conditions
        if step.condition:
            try:
                condition_str = context.substitute(step.condition)
                should_run = False
                if condition_str is not None:
                    if isinstance(condition_str, bool):
                        should_run = condition_str
                    else:
                        s = str(condition_str).strip().lower()
                        should_run = s == "true" or (s != "false" and bool(s))

                if not should_run:
                    return StepDecision.SKIP
            except Exception as e:
                logger.error(f"Failed to evaluate condition for '{step.step_id}': {e}")
                return StepDecision.SKIP

        # 3. Check approval
        if step.requires_approval:
            approvals = context.variables.get("__approvals__", [])
            is_approved = False
            if isinstance(approvals, list) and step.step_id in approvals:
                is_approved = True
            elif isinstance(approvals, (set, dict)) and step.step_id in approvals:
                is_approved = True

            if not is_approved:
                return StepDecision.SUSPEND

        return StepDecision.RUN

    async def _execute_step(self, step: WorkflowStep, context: WorkflowContext) -> None:
        """Execute a single workflow step with retry logic."""
        logger.info(f"Executing step: {step.step_id} (tool: {step.tool_name})")
        context.step_status[step.step_id] = StepStatus.RUNNING

        try:
            parameters = context.substitute(step.parameters)
        except Exception as e:
            logger.error(f"Failed to substitute parameters for '{step.step_id}': {e}")
            context.set_error(step.step_id, e)
            return

        last_error = None
        total_attempts = step.retry_count + 1

        for attempt in range(total_attempts):
            try:
                if attempt > 0:
                    logger.info(f"Retrying step '{step.step_id}' (attempt {attempt + 1}/{total_attempts})")

                if self.tool_executor:
                    result = await self._call_tool(step.tool_name, parameters, step.timeout_seconds)
                else:
                    logger.warning(f"No tool executor configured. Mocking execution for {step.step_id}")
                    result = {"step_id": step.step_id, "parameters": parameters, "mock": True}

                context.set_result(step.step_id, result, StepStatus.SUCCESS)
                logger.info(f"Step '{step.step_id}' completed successfully")
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Step '{step.step_id}' failed (attempt {attempt + 1}): {e}")
                if attempt < step.retry_count:
                    await asyncio.sleep(2**attempt)

        error = last_error if last_error is not None else Exception(f"Step '{step.step_id}' failed")
        context.set_error(step.step_id, error)
        logger.error(f"Step '{step.step_id}' failed after {total_attempts} attempts")

    async def _call_tool(
        self, tool_name: str, parameters: dict[str, Any], timeout: int | None
    ) -> Any:
        if not self.tool_executor:
            raise RuntimeError("No tool executor configured")
        coro = self.tool_executor.execute(tool_name, parameters)
        if timeout:
            return await asyncio.wait_for(coro, timeout=timeout)
        else:
            return await coro
