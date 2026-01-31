from typing import Any

import pytest

# Import routing functions directly from the module to avoid export coupling
from orchestrator.selection.routing import choose_model, get_best_model, route_request


@pytest.fixture
def model_lists() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    local = {
        "code": ["alpha-code-model", "beta-code-model"],
        "chat": ["alpha-chat-model", "beta-chat-model"],
    }
    cloud = {
        "code": ["cloud-code-1", "cloud-code-2"],
        "chat": ["cloud-chat-1", "cloud-chat-2"],
    }
    return local, cloud


def test_route_request_detects_code_by_keywords(model_lists: tuple[dict[str, list[str]], dict[str, list[str]]]) -> None:
    local, cloud = model_lists
    text = (
        "Please write a Python script to parse a CSV and compute total payroll. "
        "Ensure deterministic behavior and verify with a unit test."
    )
    result = route_request(text, provider="local", local_models=local, cloud_models=cloud)
    assert result["route"] == "code"
    assert isinstance(result["score"], (int, float)) and result["score"] >= 2  # multiple signals present
    # Should choose first code model from local
    assert result["model"] == local["code"][0]


def test_route_request_detects_code_by_fenced_block(model_lists: tuple[dict[str, list[str]], dict[str, list[str]]]) -> None:
    local, cloud = model_lists
    text = "This is a task with code: ```print('hello')```"
    result = route_request(text, provider="cloud", local_models=local, cloud_models=cloud)
    assert result["route"] == "code"
    # Should choose first code model from cloud when provider=cloud
    assert result["model"] == cloud["code"][0]


def test_route_request_defaults_to_chat(model_lists: tuple[dict[str, list[str]], dict[str, list[str]]]) -> None:
    local, cloud = model_lists
    text = "Explain the concept of generative AI and its applications in healthcare."
    result = route_request(text, provider="local", local_models=local, cloud_models=cloud)
    assert result["route"] == "chat"
    # Should choose first chat model from local
    assert result["model"] == local["chat"][0]


def test_choose_model_uses_first_in_list(model_lists: tuple[dict[str, list[str]], dict[str, list[str]]]) -> None:
    local, cloud = model_lists
    # For code route with local provider
    model = choose_model(route="code", provider="local", local_models=local, cloud_models=cloud)
    assert model == local["code"][0]
    # For chat route with cloud provider
    model = choose_model(route="chat", provider="cloud", local_models=local, cloud_models=cloud)
    assert model == cloud["chat"][0]


def test_get_best_model_returns_first(model_lists: tuple[dict[str, list[str]], dict[str, list[str]]]) -> None:
    local, cloud = model_lists
    # Simulate internal helper behavior explicitly
    best_local_code = get_best_model(
        route="code", provider="local", local_models=local, cloud_models=cloud
    )
    assert best_local_code == local["code"][0]
    best_cloud_chat = get_best_model(
        route="chat", provider="cloud", local_models=local, cloud_models=cloud
    )
    assert best_cloud_chat == cloud["chat"][0]


def test_selector_has_no_hardcoded_model_names(model_lists: Any) -> None:
    local, cloud = (
        {
            "code": ["weird-code-X", "another-code-Y"],
            "chat": ["strange-chat-A"],
        },
        {
            "code": ["cloud-weird-code"],
            "chat": ["cloud-strange-chat"],
        },
    )
    text = "Write Python to aggregate CSV, verify deterministically."
    result = route_request(text, provider="local", local_models=local, cloud_models=cloud)
    # Ensures the selector does not depend on any specific model naming patterns
    assert result["model"] == local["code"][0]
