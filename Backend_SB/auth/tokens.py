"""
SmartBee — JWT access & refresh tokens
────────────────────────────────────────
Two-token strategy:
  access_token  — short-lived (1 hour).  Sent in every API request header.
  refresh_token — long-lived (30 days).  Stored in an httpOnly cookie.
                  Used only to issue new access tokens without re-login.

Token payload (claims):
  sub  — user ID as string  (standard JWT subject)
  type — "access" | "refresh"  (guards against using wrong token)
  exp  — expiry timestamp  (set by python-jose automatically)
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt

from ..config import settings

TokenType = Literal["access", "refresh"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(user_id: int, token_type: TokenType) -> str:
    """Create a signed JWT for the given user and token type."""
    if token_type == "access":
        expires = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub":  str(user_id),
        "type": token_type,
        "exp":  expires,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> int:
    """
    Verify signature and expiry, confirm token type, return user_id.
    Raises JWTError on any validation failure — callers should catch it.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    if payload.get("type") != expected_type:
        raise JWTError(f"Expected {expected_type} token, got {payload.get('type')!r}")

    user_id = payload.get("sub")
    if user_id is None:
        raise JWTError("Token missing 'sub' claim")

    return int(user_id)
