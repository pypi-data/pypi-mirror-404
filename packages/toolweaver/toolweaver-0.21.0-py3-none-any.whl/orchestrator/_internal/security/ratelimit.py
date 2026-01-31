"""
Rate Limiting Module (Phase 9)
"""
import logging
import time

from fastapi import HTTPException, Request, Response, status

logger = logging.getLogger(__name__)

class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using Fixed Window algorithm.
    Suitable for single-process deployments.
    """
    def __init__(self, requests_per_minute: int = 60):
        self.rate_limit = requests_per_minute
        # Map: client_id -> (count, window_start_timestamp)
        self.requests: dict[str, tuple[int, float]] = {}
        self.window_size = 60.0  # 1 minute

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()

        # Clean up old entries (simplistic approach: only check current client)
        # Real impl might have a background cleanup task

        if client_id not in self.requests:
            self.requests[client_id] = (1, now)
            return True

        count, start_time = self.requests[client_id]

        if now - start_time > self.window_size:
            # New window
            self.requests[client_id] = (1, now)
            return True
        else:
            if count < self.rate_limit:
                self.requests[client_id] = (count + 1, start_time)
                return True
            else:
                return False

# Global instance (can be re-configured)
_limiter = InMemoryRateLimiter(requests_per_minute=60)

def configure_rate_limit(rpm: int) -> None:
    global _limiter
    _limiter = InMemoryRateLimiter(requests_per_minute=rpm)

async def check_rate_limit(request: Request, response: Response, api_key: str | None = None) -> None:
    """
    FastAPI dependency for rate limiting.
    Identifies client by API Key if present, else IP address.
    """
    if api_key:
        client_id = f"key:{api_key}"
    else:
        client_id = f"ip:{request.client.host if request.client else 'unknown'}"

    if not _limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
