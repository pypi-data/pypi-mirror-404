"""
Selection-layer routing utilities for deciding between code execution and chat LLMs.
Public API: route_request(), choose_model(), set_available_models()

Best practice: Keep heuristics in a selection module; expose a stable facade.

Model selection strategies:
  - USER: Explicit model from .env (OLLAMA_MODEL, COMPARISON_MODEL)
  - ORCHESTRATOR: Select best model from provided model lists based on route

Apps organize their available models by capability in .env and pass the structure.
No hardcoding of model names or patterns - pure flexibility.
"""

import os

CODE_KEYWORDS = [
    "write a script",
    "python",
    "pandas",
    "regex",
    "sql",
    "function",
    "class",
    "compute",
    "sum",
    "aggregate",
    "parse",
    "csv",
    "json",
    "dataset",
    "table",
    "loop",
    "import",
]
ACCURACY_KEYWORDS = ["deterministic", "verify", "unit test", "no hallucinations", "ground truth"]

# Global registry for available models. Set via set_available_models() at startup.
_available_models: dict[str, dict[str, list[str]]] = {}


def set_available_models(available_models: dict[str, dict[str, list[str]]]) -> None:
    """Register available models for orchestrator auto-selection.

    Args:
        available_models: Dict with 'local' and 'cloud' keys, each containing
                         'code' and 'chat' model lists.

    Example:
        set_available_models({
            "local": {
                "code": ["codellama:7b", "codegemma:2b"],
                "chat": ["phi3:latest", "neural-chat:latest"]
            },
            "cloud": {
                "code": ["gpt-4o"],
                "chat": ["gpt-4o", "claude-3-sonnet-20240229"]
            }
        })
    """
    global _available_models
    _available_models = available_models


def get_best_model(
    route: str,
    provider: str,
    local_models: dict[str, list[str]] | None = None,
    cloud_models: dict[str, list[str]] | None = None,
) -> str:
    """Select the best model from available list for a route.

    Selects the first (highest priority) model from the appropriate list
    based on the detected route.

    Args:
        route: 'code' or 'chat' (detected from request analysis)
        provider: 'local' (Ollama) or 'cloud' (Azure/API)
        local_models: Dict with 'code' and 'chat' model lists (optional, uses registered if not provided)
        cloud_models: Dict with 'code' and 'chat' model lists (optional, uses registered if not provided)

    Returns:
        Best model name (first in priority order for the route)
    """
    # Use provided models, or fall back to registered models
    if provider == "local":
        models_dict = local_models if local_models else _available_models.get("local", {})
    else:  # cloud
        models_dict = cloud_models if cloud_models else _available_models.get("cloud", {})

    models = models_dict.get(route, [])

    if not models:
        # Fallback defaults if nothing available for this route
        return "codellama:7b" if provider == "local" else "gpt-4o"

    return models[0]  # Highest priority (first in list)


def choose_model(
    route: str,
    provider: str = "local",
    local_models: dict[str, list[str]] | None = None,
    cloud_models: dict[str, list[str]] | None = None,
) -> str:
    """Pick a model based on route and environment configuration.

    Selection strategy:
      1. If model lists are provided, use them (preferred for explicit control)
      2. Else check MODEL_SELECTION env var:
         - 'user': Use explicit OLLAMA_MODEL or COMPARISON_MODEL from .env
         - 'orchestrator': Select from registered model lists based on route

    Args:
        route: 'code' or 'chat' (detected from request analysis)
        provider: 'local' (Ollama) or 'cloud' (Azure/API)
        local_models: Dict with 'code' and 'chat' model lists (optional)
        cloud_models: Dict with 'code' and 'chat' model lists (optional)

    Returns:
        Selected model name
    """
    # If explicit model lists are provided, always use them (highest priority)
    if local_models or cloud_models:
        return get_best_model(route, provider, local_models, cloud_models)

    selection_mode = os.getenv("MODEL_SELECTION", "user").lower()

    if selection_mode == "orchestrator":
        return get_best_model(route, provider, None, None)

    # User-explicit mode (default) - use env vars
    if route == "code":
        return os.getenv("OLLAMA_MODEL", "codellama:7b")
    return os.getenv("COMPARISON_MODEL", "gpt-4o")


def route_request(
    text: str,
    provider: str = "local",
    local_models: dict[str, list[str]] | None = None,
    cloud_models: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    """Analyze request and return best route + model for the task.

    Heuristics for route detection:
      - Presence of fenced code blocks (```) or >=2 code/accuracy keywords → code route
      - Else → chat route

    Then selects best model from provided lists for the detected route.

    Args:
        text: Request text to analyze
        provider: 'local' (Ollama) or 'cloud' (Azure/API)
        local_models: Dict with 'code' and 'chat' model lists (optional)
        cloud_models: Dict with 'code' and 'chat' model lists (optional)

    Returns:
        Dict with route, model, score, selection_mode, and available_models
    """
    t = (text or "").lower()
    score = 0
    score += sum(1 for k in CODE_KEYWORDS if k in t)
    score += sum(1 for k in ACCURACY_KEYWORDS if k in t)

    route = "code" if ("```" in text or score >= 2) else "chat"
    model = choose_model(route, provider, local_models, cloud_models)

    response = {
        "route": route,
        "model": model,
        "score": score,
        "selection_mode": os.getenv("MODEL_SELECTION", "user"),
        "provider": provider,
    }

    # Include available models for transparency
    if local_models:
        response["local_models"] = local_models
    if cloud_models:
        response["cloud_models"] = cloud_models

    return response
