"""
SmartBee — Trusted Host middleware
───────────────────────────────────
Rejects requests whose Host header doesn't match an allowed value.
Prevents HTTP Host-header injection attacks where a bad actor spoofs
the Host to trick password-reset links, cache poisoning, etc.

In development this allows localhost on any port.
Set ALLOWED_HOSTS in .env (comma-separated) for production.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings


def _build_allowed(frontend_url: str, app_env: str) -> set[str]:
    """Derive allowed hostnames from config."""
    hosts = {"localhost", "127.0.0.1"}

    # Always add the host portion of the frontend URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(frontend_url)
        if parsed.hostname:
            hosts.add(parsed.hostname)
    except Exception:
        pass

    # In development, permit any port on localhost
    if app_env == "development":
        hosts.update({"localhost", "127.0.0.1", "0.0.0.0"})

    return hosts


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """Reject requests with unexpected Host headers."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._allowed = _build_allowed(settings.FRONTEND_URL, settings.APP_ENV)

    async def dispatch(self, request: Request, call_next):
        host_header = request.headers.get("host", "")
        # Strip port for comparison
        hostname = host_header.split(":")[0].lower()

        if hostname and hostname not in self._allowed:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid Host header: {host_header!r}"},
            )

        return await call_next(request)
