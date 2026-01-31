
from typing import Any

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from orchestrator._internal.workflows.api import create_workflow_router  # noqa: E402
from orchestrator._internal.workflows.engine import WorkflowExecutor  # noqa: E402
from orchestrator._internal.workflows.persistence import FileWorkflowStore


class MockToolExecutor:
    async def execute(self, tool_name: str, params: dict[str, Any]) -> str:
        return f"executed {tool_name}"

@pytest.fixture
def store(tmp_path: Any) -> FileWorkflowStore:
    return FileWorkflowStore(tmp_path)

@pytest.fixture
def executor(store: FileWorkflowStore) -> WorkflowExecutor:
    return WorkflowExecutor(MockToolExecutor(), store)

@pytest.fixture
def api_client(executor: WorkflowExecutor, store: FileWorkflowStore) -> TestClient:
    router = create_workflow_router(executor, store)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_start_workflow(api_client: Any) -> None:
    template = {
        "name": "api_test_wf",
        "description": "test",
        "steps": [
            {
                "step_id": "step1",
                "tool_name": "test_tool",
                "parameters": {"p": "v"}
            }
        ]
    }

    response = api_client.post("/api/workflows/", json={"template": template, "inputs": {}})
    assert response.status_code == 200, response.text
    data = response.json()
    workflow_id = data["id"]
    assert workflow_id

    # Check status
    response = api_client.get(f"/api/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["id"] == workflow_id

def test_resume_workflow(api_client: Any, executor: Any, store: Any) -> None:
    # 1. Start a workflow that suspends
    template = {
        "name": "suspend_wf",
        "steps": [
            {
                "step_id": "step1",
                "tool_name": "test_tool",
                "parameters": {},
                "requires_approval": True
            }
        ]
    }

    response = api_client.post("/api/workflows/", json={"template": template, "inputs": {}})
    assert response.status_code == 200
    workflow_id = response.json()["id"]

    # 2. Check it is suspended
    response = api_client.get(f"/api/workflows/{workflow_id}")
    data = response.json()
    assert data["status"] == "suspended"
    assert data["suspended_on"]["step_id"] == "step1"

    # 3. Resume
    response = api_client.post(
        f"/api/workflows/{workflow_id}/resume",
        json={"inputs": {"__approvals__": ["step1"]}}
    )
    assert response.status_code == 200

    # 4. Verify result in store
    # Since TestClient runs background tasks, it should be done
    context = store.load_state(workflow_id)
    assert context is not None
    status = context.get_status("step1")
    assert status is not None
    assert status.value == "success"

