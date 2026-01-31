"""Tool call validation for production use.

This module provides validation of tool calls against tool schemas,
ensuring parameters match requirements before execution.
"""

from dataclasses import dataclass
from typing import Any

from orchestrator.adapters.orchestrator_interface import ToolCall, ToolSchema


@dataclass
class ValidationError:
    """Represents a validation error."""

    code: str
    """Error code (e.g., 'missing_required', 'invalid_type', 'invalid_enum')."""

    field: str
    """Parameter name that caused the error."""

    message: str
    """Human-readable error message."""

    expected: str | None = None
    """Expected value or type."""

    actual: str | None = None
    """Actual value or type provided."""

    def __str__(self) -> str:
        """String representation."""
        return f"{self.code}:{self.field} - {self.message}"


class ToolCallValidator:
    """Validate tool calls against tool schemas."""

    @staticmethod
    def validate(tool_call: ToolCall, schema: ToolSchema) -> tuple[bool, list[ValidationError]]:
        """
        Validate a tool call against a schema.

        Args:
            tool_call: Tool call to validate
            schema: Tool schema defining requirements

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors: list[ValidationError] = []

        # Get required parameters
        required = schema.required or []
        provided_params = tool_call.parameters or {}
        schema_properties = schema.parameters.get("properties", {})

        # Check required parameters
        for param_name in required:
            if param_name not in provided_params:
                errors.append(
                    ValidationError(
                        code="missing_required",
                        field=param_name,
                        message=f"Required parameter '{param_name}' is missing",
                        expected=f"value for {param_name}",
                        actual="not provided",
                    )
                )

        # Check parameter types and values
        for param_name, param_value in provided_params.items():
            if param_name not in schema_properties:
                # Unknown parameter - optional, just warn
                continue

            param_schema = schema_properties[param_name]
            errors.extend(
                ToolCallValidator._validate_parameter(param_name, param_value, param_schema)
            )

        return len(errors) == 0, errors

    @staticmethod
    def _validate_parameter(
        param_name: str, param_value: Any, param_schema: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate a single parameter against its schema."""
        errors: list[ValidationError] = []

        expected_type = param_schema.get("type")

        # Check type
        if expected_type:
            actual_type = ToolCallValidator._get_type_name(param_value)
            if not ToolCallValidator._type_matches(param_value, expected_type):
                errors.append(
                    ValidationError(
                        code="invalid_type",
                        field=param_name,
                        message=f"Parameter '{param_name}' has wrong type",
                        expected=expected_type,
                        actual=actual_type,
                    )
                )
                return errors  # Can't validate further if type is wrong

        # Check enum values
        if "enum" in param_schema:
            allowed_values = param_schema["enum"]
            if param_value not in allowed_values:
                errors.append(
                    ValidationError(
                        code="invalid_enum",
                        field=param_name,
                        message=f"Parameter '{param_name}' must be one of {allowed_values}",
                        expected=f"one of {allowed_values}",
                        actual=str(param_value),
                    )
                )

        # Check string length
        if expected_type == "string":
            if "minLength" in param_schema and len(param_value) < param_schema["minLength"]:
                errors.append(
                    ValidationError(
                        code="too_short",
                        field=param_name,
                        message=f"Parameter '{param_name}' is too short (min: {param_schema['minLength']})",
                        expected=f">= {param_schema['minLength']} characters",
                        actual=f"{len(param_value)} characters",
                    )
                )

            if "maxLength" in param_schema and len(param_value) > param_schema["maxLength"]:
                errors.append(
                    ValidationError(
                        code="too_long",
                        field=param_name,
                        message=f"Parameter '{param_name}' is too long (max: {param_schema['maxLength']})",
                        expected=f"<= {param_schema['maxLength']} characters",
                        actual=f"{len(param_value)} characters",
                    )
                )

        # Check numeric ranges
        if expected_type in ("integer", "number"):
            if "minimum" in param_schema and param_value < param_schema["minimum"]:
                errors.append(
                    ValidationError(
                        code="too_small",
                        field=param_name,
                        message=f"Parameter '{param_name}' is too small (min: {param_schema['minimum']})",
                        expected=f">= {param_schema['minimum']}",
                        actual=str(param_value),
                    )
                )

            if "maximum" in param_schema and param_value > param_schema["maximum"]:
                errors.append(
                    ValidationError(
                        code="too_large",
                        field=param_name,
                        message=f"Parameter '{param_name}' is too large (max: {param_schema['maximum']})",
                        expected=f"<= {param_schema['maximum']}",
                        actual=str(param_value),
                    )
                )

        return errors

    @staticmethod
    def _type_matches(value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type."""
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        if expected_type == "array":
            return isinstance(value, list)
        if expected_type == "object":
            return isinstance(value, dict)
        return True  # Unknown type, assume valid

    @staticmethod
    def _get_type_name(value: Any) -> str:
        """Get the type name for error messages."""
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return type(value).__name__

    @staticmethod
    def get_error_summary(errors: list[ValidationError]) -> str:
        """Get a summary of validation errors."""
        if not errors:
            return ""

        lines = ["Validation errors:"]
        for error in errors:
            lines.append(f"  - {error}")

        return "\n".join(lines)

    @staticmethod
    def is_valid(tool_call: ToolCall, schema: ToolSchema) -> bool:
        """Check if a tool call is valid."""
        is_valid, _ = ToolCallValidator.validate(tool_call, schema)
        return is_valid

    @staticmethod
    def get_errors(tool_call: ToolCall, schema: ToolSchema) -> list[ValidationError]:
        """Get all validation errors for a tool call."""
        _, errors = ToolCallValidator.validate(tool_call, schema)
        return errors
