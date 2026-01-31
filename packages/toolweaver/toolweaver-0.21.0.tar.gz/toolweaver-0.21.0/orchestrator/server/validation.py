#!/usr/bin/env python3
"""
Input Validation Middleware for Skills API (Phase 4.3.3)

This module provides comprehensive input validation for API requests:
- JSON schema validation against defined schemas
- String sanitization to prevent injection attacks
- Type checking and range validation
- Maximum payload size enforcement
- Request validation decorator
"""

import logging
import os
import re
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify, request

# Configure logging
logging.basicConfig(
    level=os.getenv("INPUT_VALIDATION_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration from environment
MAX_PAYLOAD_SIZE = int(os.getenv("MAX_PAYLOAD_SIZE_MB", "10")) * 1024 * 1024  # Convert MB to bytes
STRICT_VALIDATION = os.getenv("STRICT_VALIDATION", "true").lower() == "true"
SANITIZE_STRINGS = os.getenv("SANITIZE_STRINGS", "true").lower() == "true"
INPUT_VALIDATION_DEBUG = os.getenv("INPUT_VALIDATION_DEBUG", "false").lower() == "true"

# JSON schemas for different endpoints
SCHEMAS: dict[str, dict[str, Any]] = {
    "execute_skill": {
        "type": "object",
        "properties": {
            "input": {"type": ["string", "object", "array"]},
            "parameters": {"type": "object"},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
        },
        "required": [],  # input is optional
    },
    "create_collection": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 100},
            "description": {"type": "string", "maxLength": 500},
        },
        "required": ["name"],
    },
    "add_skill_to_collection": {
        "type": "object",
        "properties": {"skill_id": {"type": "string", "minLength": 1, "maxLength": 100}},
        "required": [],
    },
    "rate_skill": {
        "type": "object",
        "properties": {"rating": {"type": "integer", "minimum": 1, "maximum": 5}},
        "required": ["rating"],
    },
}

# Dangerous patterns that might indicate injection attacks
INJECTION_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # XSS
    r"javascript:",  # JavaScript protocol
    r"on\w+\s*=",  # Event handlers
    r"<!--.*?-->",  # HTML comments
    r"\$\{.*?\}",  # Template injection
    r"__import__",  # Python code injection
    r"eval\s*\(",  # Eval injection
    r"exec\s*\(",  # Exec injection
]


class InputValidator:
    """Validates API request inputs against schemas and security rules"""

    def __init__(self) -> None:
        """Initialize validator with compiled regex patterns"""
        self.injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
        ]

    def validate_payload_size(self, content_length: int | None) -> tuple[bool, str | None]:
        """
        Check if payload size is within limits

        Returns:
            (valid: bool, error_message: str or None)
        """
        if content_length is None:
            return True, None

        if content_length > MAX_PAYLOAD_SIZE:
            error = f"Payload too large: {content_length} bytes (max: {MAX_PAYLOAD_SIZE})"
            logger.warning(error)
            return False, error

        return True, None

    def sanitize_string(self, value: str) -> str:
        """
        Sanitize string to prevent injection attacks

        Returns:
            Sanitized string
        """
        if not SANITIZE_STRINGS:
            return value

        # Remove null bytes
        value = value.replace("\x00", "")

        # Check for injection patterns
        for pattern in self.injection_patterns:
            if pattern.search(value):
                if INPUT_VALIDATION_DEBUG:
                    logger.debug(f"Removed potentially dangerous pattern: {pattern.pattern}")
                value = pattern.sub("", value)

        # Limit string length (prevent DOS via huge strings)
        if len(value) > 100000:
            logger.warning(f"String truncated from {len(value)} to 100000 characters")
            value = value[:100000]

        return value

    def validate_type(self, value: Any, expected_types: list[str]) -> tuple[bool, str | None]:
        """
        Validate value type

        Args:
            value: Value to validate
            expected_types: List of expected types ('string', 'integer', 'object', 'array', 'boolean', 'number')

        Returns:
            (valid: bool, error_message: str or None)
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
            "null": type(None),
        }

        for expected_type in expected_types:
            python_type = type_mapping.get(expected_type)
            if python_type and isinstance(value, python_type):  # type: ignore[arg-type]
                return True, None

        return False, f"Invalid type: expected {expected_types}, got {type(value).__name__}"

    def validate_range(
        self, value: int, minimum: int | None, maximum: int | None
    ) -> tuple[bool, str | None]:
        """
        Validate integer/number is within range

        Returns:
            (valid: bool, error_message: str or None)
        """
        if minimum is not None and value < minimum:
            return False, f"Value {value} is below minimum {minimum}"

        if maximum is not None and value > maximum:
            return False, f"Value {value} exceeds maximum {maximum}"

        return True, None

    def validate_string_constraints(
        self, value: str, min_length: int | None, max_length: int | None
    ) -> tuple[bool, str | None]:
        """
        Validate string length constraints

        Returns:
            (valid: bool, error_message: str or None)
        """
        if min_length is not None and len(value) < min_length:
            return False, f"String too short: {len(value)} < {min_length}"

        if max_length is not None and len(value) > max_length:
            return False, f"String too long: {len(value)} > {max_length}"

        return True, None

    def validate_property(self, value: Any, schema: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate a single property against its schema

        Returns:
            (valid: bool, error_message: str or None)
        """
        # Type validation
        expected_types = schema.get("type")
        if expected_types:
            if isinstance(expected_types, str):
                expected_types = [expected_types]
            valid, error = self.validate_type(value, expected_types)
            if not valid:
                return False, error

        # Range validation for integers/numbers
        if isinstance(value, (int, float)):
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None or maximum is not None:
                valid, error = self.validate_range(int(value), minimum, maximum)
                if not valid:
                    return False, error

        # String constraints
        if isinstance(value, str):
            min_length = schema.get("minLength")
            max_length = schema.get("maxLength")
            if min_length is not None or max_length is not None:
                valid, error = self.validate_string_constraints(value, min_length, max_length)
                if not valid:
                    return False, error

            # Sanitize strings
            if SANITIZE_STRINGS:
                sanitized = self.sanitize_string(value)
                if sanitized != value and INPUT_VALIDATION_DEBUG:
                    logger.debug(f"String sanitized: {value[:50]}... -> {sanitized[:50]}...")

        return True, None

    def validate_against_schema(self, data: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate data against JSON schema

        Returns:
            (valid: bool, error_messages: list)
        """
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate each property
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                valid, error = self.validate_property(value, properties[key])
                if not valid:
                    errors.append(f"{key}: {error}")
            elif STRICT_VALIDATION:
                errors.append(f"Unknown field: {key}")

        return len(errors) == 0, errors

    def validate_request(self, schema_name: str) -> tuple[bool, dict[str, Any] | None, list[str]]:
        """
        Validate current Flask request

        Args:
            schema_name: Name of schema to validate against

        Returns:
            (valid: bool, sanitized_data: dict or None, error_messages: list)
        """
        # Check payload size
        content_length = request.content_length
        valid, error = self.validate_payload_size(content_length)
        if not valid:
            return False, None, [error] if error else []

        # Parse JSON
        try:
            data = request.json
        except Exception as e:
            error_msg = f"Invalid JSON: {str(e)}"
            return False, None, [error_msg]

        if data is None:
            data = {}

        # Get schema
        schema = SCHEMAS.get(schema_name)
        if not schema:
            logger.error(f"Unknown schema: {schema_name}")
            return True, data, []  # No schema = no validation

        # Validate against schema
        valid, errors = self.validate_against_schema(data, schema)

        # Sanitize strings in data
        if SANITIZE_STRINGS and valid:
            data = self._sanitize_dict(data)

        return valid, data, errors

    def _sanitize_dict(self, data: Any) -> Any:
        """Recursively sanitize strings in nested data structures"""
        if isinstance(data, str):
            return self.sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self._sanitize_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict(item) for item in data]
        else:
            return data


# Global validator instance
_validator: InputValidator | None = None


def get_validator() -> InputValidator:
    """Get or create input validator singleton"""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def validate_input(schema_name: str) -> Callable[..., Any]:
    """
    Decorator to validate request input against a schema

    The validated and sanitized data is available via:
    - request.json (original, but validated)
    - g.validated_data (sanitized version)

    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_input('create_collection')
        def my_endpoint():
            data = request.json  # Already validated
            # Or use: data = g.validated_data  # Sanitized version
            return {'data': 'value'}
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            validator = get_validator()

            # Validate request
            valid, sanitized_data, errors = validator.validate_request(schema_name)

            if not valid:
                logger.warning(f"Validation failed for {schema_name}: {errors}")
                return jsonify(
                    {"success": False, "error": "Validation failed", "details": errors}
                ), 400

            # Store validated data in flask.g for endpoint to use
            if sanitized_data is not None:
                from flask import g

                g.validated_data = sanitized_data

            # Call original function
            return f(*args, **kwargs)

        return decorated_function

    return decorator
