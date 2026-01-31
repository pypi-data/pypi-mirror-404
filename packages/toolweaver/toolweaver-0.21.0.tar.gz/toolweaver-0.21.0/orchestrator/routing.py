"""
Routing utilities for deciding between code execution and chat LLMs.
Public API: route_request(), choose_model()
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


def choose_model(route: str) -> str:
    """Pick a model based on route and environment configuration."""
    if route == "code":
        return os.getenv("OLLAMA_MODEL", "codellama:7b")
    # Default chat model identifier; upstream clients may remap to Azure OpenAI
    return os.getenv("COMPARISON_MODEL", "gpt-4o")


def route_request(text: str) -> dict[str, object]:
    """Return routing decision with a confidence score and selected model.

    Heuristics:
      - Presence of fenced code blocks (```) or >=2 keyword hits → code route
      - Else → chat route
    """
    t = (text or "").lower()
    score = 0
    score += sum(1 for k in CODE_KEYWORDS if k in t)
    score += sum(1 for k in ACCURACY_KEYWORDS if k in t)

    route = "code" if ("```" in text or score >= 2) else "chat"
    model = choose_model(route)
    return {"route": route, "model": model, "score": score}
