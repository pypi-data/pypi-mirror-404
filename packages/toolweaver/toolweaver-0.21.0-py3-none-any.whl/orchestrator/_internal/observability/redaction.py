"""
Secrets & PII Redaction Utility (Phase 7.3)

Provides centralized logic for scrubbing sensitive information from logs,
traces, and error messages.

Features:
- Regex-based pattern matching for API keys, emails, etc.
- Key-based redaction for dictionaries (e.g. "password", "api_key").
- Recursive structure traversal (dicts, lists).

Usage:
    from orchestrator._internal.observability.redaction import redact_data

    clean_data = redact_data(original_data)
"""

import re
from typing import Any

# Patterns to identify sensitive strings
PATTERNS = {
    # OpenAI/Anthropic keys often start with specific prefixes
    "API_KEY": r"(sk-[a-zA-Z0-9\-_]{20,})",
    "BEARER_TOKEN": r"(Bearer\s+[a-zA-Z0-9\-\._~+/]+=*)",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    # Basic Credit Card (MasterCard/Visa) - simplified to avoid false positives
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
}

# Keys in dictionaries that are always considered sensitive
SENSITIVE_KEYS = {
    "api_key",
    "auth_token",
    "access_token",
    "password",
    "secret",
    "client_secret",
    "authorization",
    "cookie",
    "token",
}

REDACTED_STR = "[REDACTED]"


def redact_text(text: Any) -> Any:
    """
    Redact sensitive patterns from a string.

    Args:
        text: Input string

    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return text

    for name, pattern in PATTERNS.items():
        # Replace the match with [REDACTED:<TYPE>] or just [REDACTED]
        # We use a lambda to support getting the matched group length if we wanted partial redaction
        text = re.sub(pattern, f"[REDACTED:{name}]", text)
    return text


def redact_data(data: Any) -> Any:
    """
    Recursively redact sensitive information from data structures.

    Args:
        data: Dict, list, or primitive value

    Returns:
        Copy of data with sensitive fields redacted
    """
    if isinstance(data, dict):
        return _redact_dict(data)
    elif isinstance(data, list):
        return [_redact_data_recursive(item) for item in data]
    elif isinstance(data, str):
        return redact_text(data)
    else:
        return data


def _redact_data_recursive(data: Any) -> Any:
    """Helper for recursion to avoid redundant type checks."""
    if isinstance(data, dict):
        return _redact_dict(data)
    elif isinstance(data, list):
        return [_redact_data_recursive(item) for item in data]
    elif isinstance(data, str):
        return redact_text(data)
    else:
        return data


def _redact_dict(data: dict[Any, Any]) -> dict[Any, Any]:
    """Redact a dictionary."""
    # Create a shallow copy first, deep structure built recursively
    new_data: dict[Any, Any] = {}

    for k, v in data.items():
        # Check if key itself triggers redaction
        if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
            new_data[k] = REDACTED_STR
        else:
            new_data[k] = _redact_data_recursive(v)

    return new_data
