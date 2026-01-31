#!/usr/bin/env python3
"""
Rate Limiting Middleware for Skills API (Phase 4.3.2)

This module provides Redis-backed rate limiting for the Skills API with:
- Per-API-key quotas (configurable)
- Per-IP address quotas (configurable)
- Sliding window counter algorithm
- 429 Too Many Requests responses with Retry-After headers
- Admin endpoint bypass
- Configurable reset intervals
"""

import logging
import os
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, cast

from flask import jsonify, request

redis: Any | None = None

try:
    import redis as _redis
except ImportError:
    REDIS_AVAILABLE = False
else:
    redis = _redis
    REDIS_AVAILABLE = True

# Configure logging
logging.basicConfig(
    level=os.getenv("RATE_LIMITER_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000"))
RATE_LIMIT_REQUESTS_PER_DAY = int(os.getenv("RATE_LIMIT_REQUESTS_PER_DAY", "10000"))
RATE_LIMIT_PER_IP = os.getenv("RATE_LIMIT_PER_IP", "true").lower() == "true"
RATE_LIMIT_DEBUG = os.getenv("RATE_LIMIT_DEBUG", "false").lower() == "true"

# Admin endpoints that bypass rate limiting
ADMIN_ENDPOINTS = {
    "/api/health",
    "/api/system/info",
}


class RateLimitValidator:
    """Redis-backed rate limiting validator"""

    def __init__(self, redis_url: str = REDIS_URL) -> None:
        """Initialize Redis connection for rate limiting"""
        try:
            self.redis_client: Any | None = cast(Any, redis).from_url(
                redis_url, decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Rate limiter connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            logger.warning("Rate limiting will be disabled")
            self.redis_client = None

    def _get_identifier(self, api_key: str | None = None, ip_address: str | None = None) -> str:
        """Get rate limit identifier (API key or IP address)"""
        if api_key:
            return f"ratelimit:api_key:{api_key}"
        elif ip_address and RATE_LIMIT_PER_IP:
            return f"ratelimit:ip:{ip_address}"
        else:
            return "ratelimit:default"

    def _get_window_keys(self, identifier: str) -> tuple[str, str, str]:
        """Get Redis keys for different time windows"""
        now = datetime.now()
        minute_key = f"{identifier}:minute:{now.strftime('%Y%m%d%H%M')}"
        hour_key = f"{identifier}:hour:{now.strftime('%Y%m%d%H')}"
        day_key = f"{identifier}:day:{now.strftime('%Y%m%d')}"
        return minute_key, hour_key, day_key

    def check_rate_limit(
        self, api_key: str | None = None, ip_address: str | None = None
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Check if request should be rate limited

        Returns:
            (allowed: bool, rate_limit_info: dict or None)
            If not allowed, rate_limit_info contains:
            - retry_after: seconds to wait
            - limit_type: 'minute', 'hour', or 'day'
            - current_count: current request count
            - limit: max requests allowed
        """
        if not RATE_LIMIT_ENABLED or not self.redis_client:
            return True, None

        identifier = self._get_identifier(api_key, ip_address)
        minute_key, hour_key, day_key = self._get_window_keys(identifier)

        try:
            # Get current counts
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)

            # Check limits
            if minute_count >= RATE_LIMIT_REQUESTS_PER_MINUTE:
                retry_after = 60 - (datetime.now().second or 1)
                if RATE_LIMIT_DEBUG:
                    logger.debug(
                        f"Rate limit exceeded (minute): {identifier} "
                        f"({minute_count}/{RATE_LIMIT_REQUESTS_PER_MINUTE})"
                    )
                return False, {
                    "retry_after": max(1, retry_after),
                    "limit_type": "minute",
                    "current_count": minute_count,
                    "limit": RATE_LIMIT_REQUESTS_PER_MINUTE,
                }

            if hour_count >= RATE_LIMIT_REQUESTS_PER_HOUR:
                retry_after = 3600 - (datetime.now().minute * 60 + datetime.now().second or 1)
                if RATE_LIMIT_DEBUG:
                    logger.debug(
                        f"Rate limit exceeded (hour): {identifier} "
                        f"({hour_count}/{RATE_LIMIT_REQUESTS_PER_HOUR})"
                    )
                return False, {
                    "retry_after": max(1, retry_after),
                    "limit_type": "hour",
                    "current_count": hour_count,
                    "limit": RATE_LIMIT_REQUESTS_PER_HOUR,
                }

            if day_count >= RATE_LIMIT_REQUESTS_PER_DAY:
                retry_after = 86400 - (
                    datetime.now().hour * 3600 + datetime.now().minute * 60 + datetime.now().second
                    or 1
                )
                if RATE_LIMIT_DEBUG:
                    logger.debug(
                        f"Rate limit exceeded (day): {identifier} "
                        f"({day_count}/{RATE_LIMIT_REQUESTS_PER_DAY})"
                    )
                return False, {
                    "retry_after": max(1, retry_after),
                    "limit_type": "day",
                    "current_count": day_count,
                    "limit": RATE_LIMIT_REQUESTS_PER_DAY,
                }

            # Increment counters (set expiry for automatic cleanup)
            self.redis_client.incr(minute_key)
            self.redis_client.expire(minute_key, 60)

            self.redis_client.incr(hour_key)
            self.redis_client.expire(hour_key, 3600)

            self.redis_client.incr(day_key)
            self.redis_client.expire(day_key, 86400)

            return True, {
                "requests_remaining_minute": RATE_LIMIT_REQUESTS_PER_MINUTE - minute_count - 1,
                "requests_remaining_hour": RATE_LIMIT_REQUESTS_PER_HOUR - hour_count - 1,
                "requests_remaining_day": RATE_LIMIT_REQUESTS_PER_DAY - day_count - 1,
                "minute_limit": RATE_LIMIT_REQUESTS_PER_MINUTE,
                "hour_limit": RATE_LIMIT_REQUESTS_PER_HOUR,
                "day_limit": RATE_LIMIT_REQUESTS_PER_DAY,
            }

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open - allow request if rate limiter fails
            return True, None

    def reset_limits(self, api_key: str | None = None, ip_address: str | None = None) -> bool:
        """Reset rate limits for an identifier (admin function)"""
        if not self.redis_client:
            return False

        identifier = self._get_identifier(api_key, ip_address)

        try:
            # Delete all rate limit keys for this identifier
            pattern = f"{identifier}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
            logger.info(f"Rate limits reset for {identifier}")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limits: {e}")
            return False


# Global rate limiter instance
_validator: RateLimitValidator | None = None


def get_validator() -> RateLimitValidator:
    """Get or create rate limiter singleton"""
    global _validator
    if _validator is None:
        _validator = RateLimitValidator()
    return _validator


def rate_limit(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to enforce rate limiting on an endpoint

    Usage:
        @app.route('/api/endpoint', methods=['GET'])
        @rate_limit
        def my_endpoint():
            return {'data': 'value'}
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Check if endpoint is exempt from rate limiting
        if request.path in ADMIN_ENDPOINTS:
            return f(*args, **kwargs)

        # Get rate limiter
        validator = get_validator()

        # Extract API key and IP address
        api_key = request.headers.get("X-API-Key")
        ip_address = request.remote_addr

        # Check rate limit
        allowed, limit_info = validator.check_rate_limit(api_key, ip_address)

        if not allowed and limit_info:
            retry_after = limit_info["retry_after"]
            response = jsonify(
                {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "limit_type": limit_info["limit_type"],
                    "current_count": limit_info["current_count"],
                    "limit": limit_info["limit"],
                    "retry_after_seconds": retry_after,
                }
            )
            response.status_code = 429
            response.headers["Retry-After"] = str(retry_after)

            logger.warning(
                f"Rate limit exceeded for {ip_address}: "
                f"{limit_info['limit_type']} "
                f"({limit_info['current_count']}/{limit_info['limit']})"
            )

            return response

        # Add rate limit headers to response
        def add_rate_limit_headers(response: Any) -> Any:
            if limit_info and "requests_remaining_minute" in limit_info:
                response.headers["X-RateLimit-Limit-Minute"] = str(limit_info["minute_limit"])
                response.headers["X-RateLimit-Remaining-Minute"] = str(
                    limit_info["requests_remaining_minute"]
                )
                response.headers["X-RateLimit-Limit-Hour"] = str(limit_info["hour_limit"])
                response.headers["X-RateLimit-Remaining-Hour"] = str(
                    limit_info["requests_remaining_hour"]
                )
                response.headers["X-RateLimit-Limit-Day"] = str(limit_info["day_limit"])
                response.headers["X-RateLimit-Remaining-Day"] = str(
                    limit_info["requests_remaining_day"]
                )
            return response

        # Call original function
        response = f(*args, **kwargs)

        # Handle different response types
        if isinstance(response, tuple):
            # Response is (data, status_code) or (data, status_code, headers)
            data, status_code = response[:2]
            headers = response[2] if len(response) > 2 else {}

            if isinstance(headers, dict):
                # Add rate limit headers to existing headers dict
                headers.update(
                    {
                        "X-RateLimit-Limit-Minute": str(
                            limit_info.get("minute_limit", RATE_LIMIT_REQUESTS_PER_MINUTE)
                        )
                        if limit_info
                        else "",
                        "X-RateLimit-Remaining-Minute": str(
                            limit_info.get("requests_remaining_minute", 0)
                        )
                        if limit_info
                        else "",
                    }
                )
                return (data, status_code, headers)
            else:
                # Headers is a list or something else, return as-is
                return response
        else:
            # Response is just data, wrap with rate limit headers
            return add_rate_limit_headers(response)

    return decorated_function


def validate_rate_limit(
    api_key: str | None = None, ip_address: str | None = None
) -> tuple[bool, dict[str, Any] | None]:
    """Convenience function to check rate limits"""
    validator = get_validator()
    return validator.check_rate_limit(api_key, ip_address)
