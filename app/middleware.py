"""
HTTP middleware for rate limiting and security response headers.

RateLimitMiddleware  — sliding-window per-IP rate limiter (in-memory).
                       Bypassed entirely when DISABLE_SECURITY=true.
                       For production, replace with a Redis-backed solution
                       (e.g. slowapi + redis) so limits survive restarts
                       and work correctly behind multiple workers.

SecurityHeadersMiddleware — adds a conservative set of security headers to
                            every response, including error responses.
"""

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Module-level store so tests can reset it between runs.
_rate_limit_store: dict[str, deque] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter keyed by client IP address."""

    async def dispatch(self, request: Request, call_next):
        from app.config import settings  # read at call-time so tests can monkeypatch

        if settings.disable_security:
            return await call_next(request)

        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _rate_limit_store[key]

        # Evict timestamps outside the current window
        while window and window[0] < now - settings.rate_limit_period:
            window.popleft()

        if len(window) >= settings.rate_limit_calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests — please slow down."},
                headers={"Retry-After": str(settings.rate_limit_period)},
            )

        window.append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security-related HTTP response headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
