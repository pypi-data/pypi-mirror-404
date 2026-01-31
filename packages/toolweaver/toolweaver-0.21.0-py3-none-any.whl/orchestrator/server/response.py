#!/usr/bin/env python3
"""
Response Envelope Middleware for Skills API (Phase 4.3.4)

This module provides standardized API response formatting with:
- Consistent response structure across all endpoints
- Request ID tracking for debugging
- Timestamp information
- API version info
- Standard error format
- Success/failure indicators
- Metadata (execution time, rate limits, etc.)
"""

import logging
import os
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from typing import TYPE_CHECKING, Any

from flask import Response, g, jsonify

if TYPE_CHECKING:
    from flask import Flask

# Configure logging
logging.basicConfig(
    level=os.getenv("RESPONSE_ENVELOPE_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration from environment
API_VERSION = os.getenv("API_VERSION", "1.0.0")
INCLUDE_TIMING = os.getenv("INCLUDE_TIMING", "true").lower() == "true"
INCLUDE_REQUEST_ID = os.getenv("INCLUDE_REQUEST_ID", "true").lower() == "true"
RESPONSE_ENVELOPE_DEBUG = os.getenv("RESPONSE_ENVELOPE_DEBUG", "false").lower() == "true"


class ResponseEnvelope:
    """Standard response envelope for API responses"""

    @staticmethod
    def success(
        data: Any,
        message: str | None = None,
        status_code: int = 200,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Create a success response envelope

        Args:
            data: Response data (any JSON-serializable object)
            message: Optional success message
            status_code: HTTP status code (default: 200)
            metadata: Optional additional metadata

        Returns:
            (response_dict, status_code)
        """
        envelope: dict[str, Any] = {
            "success": True,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if message:
            envelope["message"] = message

        if INCLUDE_REQUEST_ID:
            envelope["request_id"] = getattr(g, "request_id", None)

        if INCLUDE_TIMING and hasattr(g, "request_start_time"):
            elapsed = (time.time() - g.request_start_time) * 1000  # ms
            envelope["timing"] = {"elapsed_ms": round(elapsed, 2)}

        envelope["api_version"] = API_VERSION

        if metadata:
            envelope["metadata"] = metadata

        return envelope, status_code

    @staticmethod
    def error(
        error_message: str,
        error_code: str | None = None,
        status_code: int = 500,
        details: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Create an error response envelope

        Args:
            error_message: Human-readable error message
            error_code: Machine-readable error code (e.g., 'VALIDATION_ERROR')
            status_code: HTTP status code (default: 500)
            details: Optional additional error details
            metadata: Optional additional metadata

        Returns:
            (response_dict, status_code)
        """
        envelope: dict[str, Any] = {
            "success": False,
            "error": {
                "message": error_message,
                "code": error_code or f"ERROR_{status_code}",
            },
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if details:
            envelope["error"]["details"] = details

        if INCLUDE_REQUEST_ID:
            envelope["request_id"] = getattr(g, "request_id", None)

        if INCLUDE_TIMING and hasattr(g, "request_start_time"):
            elapsed = (time.time() - g.request_start_time) * 1000  # ms
            envelope["timing"] = {"elapsed_ms": round(elapsed, 2)}

        envelope["api_version"] = API_VERSION

        if metadata:
            envelope["metadata"] = metadata

        return envelope, status_code

    @staticmethod
    def paginated(
        items: list[Any],
        total: int,
        page: int,
        per_page: int,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Create a paginated response envelope

        Args:
            items: List of items for current page
            total: Total number of items across all pages
            page: Current page number (1-indexed)
            per_page: Items per page
            message: Optional message
            metadata: Optional additional metadata

        Returns:
            (response_dict, status_code)
        """
        pagination = {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1,
        }

        data = {"items": items, "pagination": pagination}

        return ResponseEnvelope.success(data, message, 200, metadata)


def init_request_context() -> None:
    """Initialize request context with ID and start time"""
    if INCLUDE_REQUEST_ID:
        g.request_id = str(uuid.uuid4())

    if INCLUDE_TIMING:
        g.request_start_time = time.time()


def with_envelope(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to wrap endpoint responses in standard envelope

    The decorated function can return:
    - Just data: return {'key': 'value'} or return [items]
    - Data with status: return data, 201
    - Data with status and headers: return data, 201, headers

    All will be wrapped in the standard envelope format.

    Usage:
        @app.route('/api/endpoint')
        @with_envelope
        def my_endpoint():
            return {'data': 'value'}  # Automatically wrapped
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Initialize request context
        init_request_context()

        try:
            # Call original function
            result = f(*args, **kwargs)

            # Parse result (could be data, (data, status), or (data, status, headers))
            if isinstance(result, tuple):
                if len(result) == 2:
                    data, status_code = result
                    headers: dict[str, Any] = {}
                elif len(result) == 3:
                    data, status_code, headers = result
                else:
                    # Unknown format, return as-is
                    return result
            else:
                data = result
                status_code = 200
                headers = {}

            # Check if response is already a Flask Response object
            if isinstance(data, Response):
                return data

            # Check if data is already in envelope format (has 'success' key)
            if isinstance(data, dict) and "success" in data:
                # Already enveloped, just add headers and return
                response = jsonify(data)
                response.status_code = status_code
                if headers:
                    for key, value in headers.items():
                        response.headers[key] = value
                return response

            # Wrap in success envelope
            envelope, status = ResponseEnvelope.success(data, status_code=status_code)

            # Create response
            response = jsonify(envelope)
            response.status_code = status

            # Add custom headers
            if headers:
                for key, value in headers.items():
                    response.headers[key] = value

            # Add standard headers
            if INCLUDE_REQUEST_ID and hasattr(g, "request_id"):
                response.headers["X-Request-ID"] = g.request_id

            return response

        except Exception as e:
            # Unexpected error - wrap in error envelope
            logger.error(f"Unhandled exception in {f.__name__}: {str(e)}", exc_info=True)

            envelope, status = ResponseEnvelope.error(
                error_message="Internal server error",
                error_code="INTERNAL_ERROR",
                status_code=500,
                details=str(e) if RESPONSE_ENVELOPE_DEBUG else None,
            )

            response = jsonify(envelope)
            response.status_code = status

            if INCLUDE_REQUEST_ID and hasattr(g, "request_id"):
                response.headers["X-Request-ID"] = g.request_id

            return response

    return decorated_function


def error_response(
    error_message: str,
    error_code: str | None = None,
    status_code: int = 400,
    details: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """
    Convenience function to create error responses

    Usage:
        @app.route('/api/endpoint')
        def my_endpoint():
            if not valid:
                return error_response("Invalid input", "VALIDATION_ERROR", 400)
            return {'data': 'value'}
    """
    return ResponseEnvelope.error(error_message, error_code, status_code, details)


def success_response(
    data: Any, message: str | None = None, status_code: int = 200
) -> tuple[dict[str, Any], int]:
    """
    Convenience function to create success responses

    Usage:
        @app.route('/api/endpoint')
        def my_endpoint():
            return success_response({'key': 'value'}, "Operation successful", 201)
    """
    return ResponseEnvelope.success(data, message, status_code)


def paginated_response(
    items: list[Any], total: int, page: int = 1, per_page: int = 20
) -> tuple[dict[str, Any], int]:
    """
    Convenience function to create paginated responses

    Usage:
        @app.route('/api/items')
        def list_items():
            items = get_items(page=1, per_page=20)
            total = get_total_items()
            return paginated_response(items, total, 1, 20)
    """
    return ResponseEnvelope.paginated(items, total, page, per_page)


# Flask app initialization helper
def init_app(app: "Flask") -> None:
    """
    Initialize response envelope for a Flask app

    This sets up:
    - Before request handler for request ID and timing
    - Error handlers for common HTTP errors

    Usage:
        from flask import Flask
        from response_envelope import init_app

        app = Flask(__name__)
        init_app(app)
    """

    @app.before_request
    def before_request() -> None:
        """Initialize request context"""
        init_request_context()

    @app.errorhandler(404)
    def not_found(e: Any) -> tuple[Any, int]:
        """Handle 404 errors"""
        envelope, status = ResponseEnvelope.error(
            error_message="Resource not found", error_code="NOT_FOUND", status_code=404
        )
        return jsonify(envelope), status

    @app.errorhandler(405)
    def method_not_allowed(e: Any) -> tuple[Any, int]:
        """Handle 405 errors"""
        envelope, status = ResponseEnvelope.error(
            error_message="Method not allowed", error_code="METHOD_NOT_ALLOWED", status_code=405
        )
        return jsonify(envelope), status

    @app.errorhandler(500)
    def internal_error(e: Any) -> tuple[Any, int]:
        """Handle 500 errors"""
        envelope, status = ResponseEnvelope.error(
            error_message="Internal server error",
            error_code="INTERNAL_ERROR",
            status_code=500,
            details=str(e) if RESPONSE_ENVELOPE_DEBUG else None,
        )
        return jsonify(envelope), status

    logger.info("Response envelope initialized for Flask app")

