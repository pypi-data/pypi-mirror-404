"""Tests for tool call validation."""


import pytest

from orchestrator.adapters.orchestrator_interface import ToolCall, ToolSchema
from orchestrator.adapters.production.validator import ToolCallValidator


class TestToolCallValidatorBasics:
    """Test basic validation functionality."""

    def test_valid_call_passes(self) -> None:
        """Test that a valid tool call passes validation."""
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
            },
            required=["input"],
        )

        tool_call = ToolCall(
            tool_name="test_tool",
            parameters={"input": "test value"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_call_detected(self) -> None:
        """Test that an invalid call is detected."""
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
            },
            required=["input"],
        )

        tool_call = ToolCall(
            tool_name="test_tool",
            parameters={},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert len(errors) > 0

    def test_validation_convenience_methods(self) -> None:
        """Test convenience methods."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={"properties": {"x": {"type": "string"}}},
            required=["x"],
        )

        valid_call = ToolCall(tool_name="test", parameters={"x": "value"})
        invalid_call = ToolCall(tool_name="test", parameters={})

        assert ToolCallValidator.is_valid(valid_call, schema) is True
        assert ToolCallValidator.is_valid(invalid_call, schema) is False
        assert len(ToolCallValidator.get_errors(invalid_call, schema)) > 0


class TestRequiredParameters:
    """Test required parameter validation."""

    def test_missing_required_parameter(self) -> None:
        """Test detection of missing required parameter."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
            required=["name", "age"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"name": "Alice"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert len(errors) == 1
        assert errors[0].code == "missing_required"
        assert errors[0].field == "age"

    def test_multiple_missing_parameters(self) -> None:
        """Test detection of multiple missing required parameters."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "string"},
                    "y": {"type": "string"},
                    "z": {"type": "string"},
                },
            },
            required=["x", "y", "z"],
        )

        tool_call = ToolCall(tool_name="test", parameters={})

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert len(errors) == 3

    def test_no_required_parameters(self) -> None:
        """Test validation with no required parameters."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "optional_param": {"type": "string"},
                },
            },
        )

        tool_call = ToolCall(tool_name="test", parameters={})

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True
        assert len(errors) == 0


class TestParameterTypes:
    """Test parameter type validation."""

    def test_string_type_valid(self) -> None:
        """Test valid string parameter."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
            required=["text"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"text": "hello"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True
        assert len(errors) == 0

    def test_string_type_invalid(self) -> None:
        """Test invalid string parameter (integer provided)."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
            required=["text"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"text": 123},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "invalid_type"

    def test_integer_type_valid(self) -> None:
        """Test valid integer parameter."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
            required=["count"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"count": 42},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_integer_type_invalid_float(self) -> None:
        """Test that float fails for integer type."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
            required=["count"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"count": 3.14},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "invalid_type"

    def test_number_type_accepts_int_and_float(self) -> None:
        """Test that number type accepts both int and float."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"value": {"type": "number"}},
            },
            required=["value"],
        )

        # Test with integer
        tool_call_int = ToolCall(
            tool_name="test",
            parameters={"value": 42},
        )
        is_valid, _ = ToolCallValidator.validate(tool_call_int, schema)
        assert is_valid is True

        # Test with float
        tool_call_float = ToolCall(
            tool_name="test",
            parameters={"value": 3.14},
        )
        is_valid, _ = ToolCallValidator.validate(tool_call_float, schema)
        assert is_valid is True

    def test_boolean_type(self) -> None:
        """Test boolean type validation."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
            },
            required=["enabled"],
        )

        # Valid
        tool_call = ToolCall(
            tool_name="test",
            parameters={"enabled": True},
        )
        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

        # Invalid (string)
        tool_call = ToolCall(
            tool_name="test",
            parameters={"enabled": "true"},
        )
        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "invalid_type"


class TestEnumValidation:
    """Test enum value validation."""

    def test_valid_enum_value(self) -> None:
        """Test valid enum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["fast", "slow", "medium"]},
                },
            },
            required=["mode"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"mode": "fast"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_enum_value(self) -> None:
        """Test invalid enum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["fast", "slow", "medium"]},
                },
            },
            required=["mode"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"mode": "turbo"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "invalid_enum"


class TestStringConstraints:
    """Test string length constraints."""

    def test_string_min_length_valid(self) -> None:
        """Test valid minimum length."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "password": {"type": "string", "minLength": 8},
                },
            },
            required=["password"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"password": "mypassword123"},
        )

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_string_min_length_invalid(self) -> None:
        """Test invalid minimum length."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "password": {"type": "string", "minLength": 8},
                },
            },
            required=["password"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"password": "short"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "too_short"

    def test_string_max_length_valid(self) -> None:
        """Test valid maximum length."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "maxLength": 20},
                },
            },
            required=["username"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"username": "user123"},
        )

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_string_max_length_invalid(self) -> None:
        """Test invalid maximum length."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "maxLength": 20},
                },
            },
            required=["username"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"username": "this_is_a_very_long_username_that_exceeds_limit"},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "too_long"


class TestNumericConstraints:
    """Test numeric range constraints."""

    def test_integer_minimum_valid(self) -> None:
        """Test valid minimum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "age": {"type": "integer", "minimum": 0},
                },
            },
            required=["age"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"age": 25},
        )

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_integer_minimum_invalid(self) -> None:
        """Test invalid minimum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "age": {"type": "integer", "minimum": 0},
                },
            },
            required=["age"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"age": -5},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "too_small"

    def test_integer_maximum_valid(self) -> None:
        """Test valid maximum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "percentage": {"type": "integer", "maximum": 100},
                },
            },
            required=["percentage"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"percentage": 75},
        )

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_integer_maximum_invalid(self) -> None:
        """Test invalid maximum value."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "percentage": {"type": "integer", "maximum": 100},
                },
            },
            required=["percentage"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"percentage": 150},
        )

        is_valid, errors = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is False
        assert errors[0].code == "too_large"


class TestValidationErrors:
    """Test validation error reporting."""

    def test_error_has_useful_information(self) -> None:
        """Test that errors contain useful information."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
            required=["count"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={"count": 150},
        )

        _, errors = ToolCallValidator.validate(tool_call, schema)
        error = errors[0]

        assert error.code == "too_large"
        assert error.field == "count"
        assert "count" in error.message
        assert error.expected == "<= 100"
        assert error.actual == "150"

    def test_error_summary(self) -> None:
        """Test error summary generation."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "string"},
                    "y": {"type": "string"},
                },
            },
            required=["x", "y"],
        )

        tool_call = ToolCall(tool_name="test", parameters={})

        _, errors = ToolCallValidator.validate(tool_call, schema)
        summary = ToolCallValidator.get_error_summary(errors)

        assert "Validation errors:" in summary
        assert len(summary.split("\n")) >= 3


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_parameters(self) -> None:
        """Test tool call with empty parameters."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={"type": "object", "properties": {}},
        )

        tool_call = ToolCall(tool_name="test", parameters={})

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_none_parameters(self) -> None:
        """Test tool call with None parameters."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={"type": "object", "properties": {}},
        )

        tool_call = ToolCall(tool_name="test", parameters=None)  # type: ignore[arg-type]

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True

    def test_extra_parameters_allowed(self) -> None:
        """Test that extra parameters don't fail validation."""
        schema = ToolSchema(
            name="test",
            description="Test",
            parameters={
                "type": "object",
                "properties": {
                    "required_param": {"type": "string"},
                },
            },
            required=["required_param"],
        )

        tool_call = ToolCall(
            tool_name="test",
            parameters={
                "required_param": "value",
                "extra_param": "not in schema",
            },
        )

        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
