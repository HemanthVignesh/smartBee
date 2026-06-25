"""
SmartBee — IP-based sliding-window rate limiter
────────────────────────────────────────────────
How it works
────────────
Each request increments an in-memory counter keyed by (IP, route_tier).
The counter is a deque of timestamps.  On every request we:
  1. Discard timestamps older than WINDOW_SECONDS.
  2. Count remaining timestamps → that's requests in the current window.
  3. If count >= limit → return HTTP 429 with Retry-After header.
  4. Otherwise append now and allow the request through.

Route tiers
───────────
  "ai"        → /analyze-email, /api/v1/chatbot/*, /api/v1/emails/*/analyze
  "sensitive"  → /api/v1/bootstrap/*, /api/v1/emails/fetch
  "general"    → everything else

This is all in-process memory so it resets on restart and is per-worker.
For multi-worker / multi-replica production: swap _store for a Redis backend.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings

# ─── Storage ──────────────────────────────────────────────────────────────────
# Key: (client_ip, tier)  →  deque of Unix timestamps
_store: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


# ─── Route classification ─────────────────────────────────────────────────────

def _classify(path: str) -> str:
    """Return the rate-limit tier for a given request path."""
    ai_prefixes = (
        "/analyze-email",
        "/api/v1/chatbot/",
        "/api/v1/emails/fetch",
    )
    ai_suffixes = ("/analyze",)

    sensitive_prefixes = (
        "/api/v1/bootstrap/",
        "/api/v1/emails/fetch",
    )

    for prefix in ai_prefixes:
        if path.startswith(prefix):
            return "ai"
    for suffix in ai_suffixes:
        if path.endswith(suffix):
            return "ai"
    for prefix in sensitive_prefixes:
        if path.startswith(prefix):
            return "sensitive"

    return "general"


def _get_limit(tier: str) -> int:
    return {
        "ai":        settings.RATE_LIMIT_AI,
        "sensitive": settings.RATE_LIMIT_SENSITIVE,
        "general":   settings.RATE_LIMIT_GENERAL,
    }.get(tier, settings.RATE_LIMIT_GENERAL)


# ─── Middleware ───────────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.

    Skips:
      - OPTIONS preflight (needed for CORS)
      - Health check  GET /
      - Any path in EXEMPT_PATHS
    """

    EXEMPT_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        path   = request.url.path
        method = request.method

        # Always let preflight and exempt paths through
        if method == "OPTIONS" or path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Identify client — trust X-Forwarded-For when behind a proxy/CDN
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        tier  = _classify(path)
        limit = _get_limit(tier)
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        now   = time.monotonic()

        key = (client_ip, tier)
        dq  = _store[key]

        # Evict timestamps outside the window
        while dq and dq[0] < now - window:
            dq.popleft()

        if len(dq) >= limit:
            retry_after = int(window - (now - dq[0])) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded ({limit} requests / {window}s). "
                              f"Retry in {retry_after}s.",
                    "tier": tier,
                    "limit": limit,
                    "window_seconds": window,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After":           str(retry_after),
                    "X-RateLimit-Limit":     str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window":    str(window),
                },
            )

        dq.append(now)

        # Add informational headers to successful responses
        response = await call_next(request)
        remaining = max(0, limit - len(dq))
        response.headers["X-RateLimit-Limit"]     = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"]    = str(window)
        response.headers["X-RateLimit-Tier"]      = tier
        return response
