"""
Tests for Redaction Utility (Phase 7.3)
"""



from orchestrator._internal.observability.redaction import redact_data, redact_text


def test_redact_text_api_key() -> None:
    """Test API key redaction in text."""
    text = "My key is sk-1234567890abcdef1234567890abcdef."
    redacted = redact_text(text)
    assert "sk-" not in redacted
    assert "[REDACTED:API_KEY]" in redacted


def test_redact_text_email() -> None:
    """Test email redaction in text."""
    text = "Contact me at user@example.com for details."
    redacted = redact_text(text)
    assert "user@example.com" not in redacted
    assert "[REDACTED:EMAIL]" in redacted


def test_redact_dict_keys() -> None:
    """Test redaction based on dictionary keys."""
    data = {
        "username": "user1",
        "api_key": "secret_value",
        "password": "password123",
        "config": {
            "secret": "deep_secret"
        }
    }
    redacted = redact_data(data)

    assert redacted["username"] == "user1"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["config"]["secret"] == "[REDACTED]"


def test_redact_recursion() -> None:
    """Test recursion through lists and dicts."""
    data = {
        "users": [
            {"id": 1, "token": "sensitive1"},
            {"id": 2, "description": "Email is bob@test.com"}
        ]
    }
    redacted = redact_data(data)

    # Check key redaction in list
    assert redacted["users"][0]["token"] == "[REDACTED]"

    # Check text pattern redaction in nested dict
    assert "bob@test.com" not in redacted["users"][1]["description"]
    assert "[REDACTED:EMAIL]" in redacted["users"][1]["description"]


def test_redact_primitives() -> None:
    """Test primitive values pass through."""
    assert redact_data(123) == 123
    assert redact_data(True) is True
    assert redact_data(None) is None
