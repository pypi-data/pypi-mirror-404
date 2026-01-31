from typing import Any
from unittest.mock import MagicMock

import pytest

from orchestrator._internal.composition.composer import TaskComposer
from orchestrator.adapters.orchestrator_interface import OrchestratorBackend, PlanResult
from orchestrator.shared.models import ToolCatalog, ToolDefinition


@pytest.fixture
def mock_backend() -> Any:
    backend = MagicMock(spec=OrchestratorBackend)
    return backend

@pytest.fixture
def tool_catalog() -> Any:
    from orchestrator.shared.models import ToolParameter

    catalog = ToolCatalog()
    catalog.add_tool(ToolDefinition(
        name="get_weather",
        type="function",
        description="Get weather for location",
        parameters=[
            ToolParameter(name="location", type="string", description="City", required=True)
        ]
    ))
    return catalog

def test_generate_plan(mock_backend: Any, tool_catalog: Any) -> None:
    # Setup mock response from LLM
    mock_code = """
async def main():
    w = await get_weather(location="Seattle")
    print(w)
"""
    reasoning_response = f"Here is the plan:\n```python\n{mock_code}\n```"

    mock_backend.plan.return_value = PlanResult(
        reasoning=reasoning_response,
        tool_calls=[]
    )

    composer = TaskComposer(mock_backend, tool_catalog)
    goal = "Check weather in Seattle"

    generated_code = composer.generate_plan(goal)

    assert "async def main():" in generated_code
    assert 'get_weather(location="Seattle")' in generated_code

    # Verify prompt construction
    mock_backend.plan.assert_called_once()
    call_args = mock_backend.plan.call_args
    user_msg = call_args.kwargs.get("user_message") or call_args.args[0]
    system_prompt = call_args.kwargs.get("system_prompt")

    assert goal in user_msg
    assert "async def get_weather(location: str)" in system_prompt
    assert "Pattern: LOOP" in system_prompt

def test_extract_code_fallback(mock_backend: Any, tool_catalog: Any) -> None:
    # Test handling of no markdown blocks but valid code-like text
    mock_code = "async def main():\n    pass"
    mock_backend.plan.return_value = PlanResult(
        reasoning=mock_code,
        tool_calls=[]
    )

    composer = TaskComposer(mock_backend, tool_catalog)
    generated_code = composer.generate_plan("Simple task")
    assert generated_code == mock_code
