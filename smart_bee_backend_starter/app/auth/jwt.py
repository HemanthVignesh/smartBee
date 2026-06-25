"""
auth/jwt.py — JWT creation and verification.

Uses python-jose (HS256).  The secret is read from JWT_SECRET in .env;
for production rotate it and keep it out of source control.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days


# ── Token creation ───────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    email: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT for the given user.

    Payload:
        sub  — user UUID (internal PK)
        email — user e-mail (convenience claim, not used for auth)
        iat  — issued-at (seconds)
        exp  — expiry  (seconds)
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)
    return token


# ── Token verification ───────────────────────────────────────────────────────

def decode_access_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT.  Returns the payload dict or None on any failure.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning(f"JWT verification failed: {exc}")
        return None
