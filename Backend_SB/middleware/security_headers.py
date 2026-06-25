"""
SmartBee — Security headers middleware
───────────────────────────────────────
Adds standard HTTP security headers to every response.
These are free hardening with zero application-logic cost.

Headers added:
  X-Content-Type-Options    → stops MIME sniffing
  X-Frame-Options           → prevents clickjacking
  X-XSS-Protection          → legacy XSS filter (belt + braces)
  Referrer-Policy           → avoids leaking URLs to third parties
  Content-Security-Policy   → restricts where scripts/styles can load from
  Permissions-Policy        → disables unused browser features
  Strict-Transport-Security → force HTTPS (omitted in dev)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["X-XSS-Protection"]       = "1; mode=block"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]     = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none';"
        )

        # Only add HSTS in production — in dev it would permanently break HTTP
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
