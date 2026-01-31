"""
Workflow API Router (Phase 8.4)
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from .engine import WorkflowExecutor
from .persistence import WorkflowStateStore
from .workflow import WorkflowContext, WorkflowTemplate

logger = logging.getLogger(__name__)

class WorkflowStartRequest(BaseModel):
    template: dict[str, Any] = Field(..., description="Workflow template definition")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Initial inputs")

class WorkflowResumeRequest(BaseModel):
    inputs: dict[str, Any] = Field(..., description="Inputs for resumption (e.g. approval data)")

class WorkflowResponse(BaseModel):
    id: str
    status: str
    result: dict[str, Any] | None = None
    errors: dict[str, str] = {}
    suspended_on: dict[str, Any] | None = None

def _build_response(workflow_id: str, context: WorkflowContext) -> WorkflowResponse:
    # Infer status
    status = "running"
    if context.suspension:
        status = "suspended"
    # If errors exist and no running steps?
    # This is a simplification.

    suspended_dict = None
    if context.suspension:
        suspended_dict = {
            "action_type": context.suspension.action_type,
            "description": context.suspension.description,
            "step_id": context.suspension.step_id,
            "schema": context.suspension.schema
        }

    return WorkflowResponse(
        id=workflow_id,
        status=status,
        result=context.step_results,
        errors={k: str(v) for k, v in context.errors.items()},
        suspended_on=suspended_dict
    )

def create_workflow_router(
    executor: WorkflowExecutor,
    store: WorkflowStateStore,
    dependencies: list[Any] | None = None
) -> APIRouter:
    router = APIRouter(prefix="/api/workflows", tags=["workflows"], dependencies=dependencies)

    @router.post("/", response_model=WorkflowResponse)  # type: ignore[untyped-decorator]
    async def start_workflow(
        request: WorkflowStartRequest, background_tasks: BackgroundTasks
    ) -> WorkflowResponse:
        workflow_id = str(uuid.uuid4())

        try:
            template = WorkflowTemplate.from_dict(request.template)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid template: {str(e)}") from e

        context = WorkflowContext(initial_variables=request.inputs)

        # Save initial state and template synchronously to ensure existence
        try:
            store.save_state(workflow_id, context)
            store.save_template(workflow_id, template)
        except Exception as e:
            logger.error(f"Failed to initialize workflow storage: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize workflow") from e

        background_tasks.add_task(
            executor.execute,
            workflow=template,
            workflow_id=workflow_id,
            context=context
        )

        return _build_response(workflow_id, context)

    @router.post("/{workflow_id}/resume", response_model=WorkflowResponse)  # type: ignore[untyped-decorator]
    async def resume_workflow(
        workflow_id: str,
        request: WorkflowResumeRequest,
        background_tasks: BackgroundTasks
    ) -> WorkflowResponse:
        context = store.load_state(workflow_id)
        if not context:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if not context.suspension:
             raise HTTPException(status_code=400, detail="Workflow is not suspended")

        template = store.load_template(workflow_id)
        if not template:
             raise HTTPException(status_code=500, detail="Workflow template definition missing")

        async def run_resume() -> None:
            try:
                await executor.resume(template, workflow_id, request.inputs)
            except Exception as e:
                logger.error(f"Background resume failed for {workflow_id}: {e}")

        background_tasks.add_task(run_resume)

        # Return current state (will update asynchronously)
        return _build_response(workflow_id, context)

    @router.get("/{workflow_id}", response_model=WorkflowResponse)  # type: ignore[untyped-decorator]
    async def get_workflow(workflow_id: str) -> WorkflowResponse:
        context = store.load_state(workflow_id)
        if not context:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return _build_response(workflow_id, context)

    return router
