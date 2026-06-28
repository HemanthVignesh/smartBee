"""
SmartBee — /api/v1/auth  router
─────────────────────────────────
POST /api/v1/auth/register   → create account → returns tokens
POST /api/v1/auth/login      → verify credentials → returns tokens
POST /api/v1/auth/refresh    → swap refresh cookie for new access token
POST /api/v1/auth/logout     → clear refresh cookie
GET  /api/v1/auth/me         → return current user profile

Token strategy
──────────────
  access_token  — returned in JSON body; stored in memory (React state / localStorage).
  refresh_token — set as httpOnly, SameSite=Lax cookie; never readable by JS.

This means XSS can't steal the refresh token, and CSRF can't abuse it
because our CORS policy only allows requests from FRONTEND_URL.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.dependencies import get_current_active_user
from ...auth.passwords import hash_password, verify_password
from ...auth.tokens import create_token, decode_token
from ...config import settings
from ...database import get_db
from ...models.orm import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_NAME = "smartbee_refresh"
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86_400  # seconds


# ─── Request / response schemas ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    id: int
    email: str
    display_name: str | None
    is_verified: bool
    created_at: str
    last_login_at: str | None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,                           # JS cannot read this
        samesite="lax",                          # CSRF protection
        secure=(settings.APP_ENV == "production"),  # HTTPS only in prod
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth/refresh",             # only sent to the refresh endpoint
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/api/v1/auth/refresh")


def _build_token_response(user: User) -> dict:
    return {
        "id":           user.id,
        "email":        user.email,
        "display_name": user.display_name,
        "is_verified":  user.is_verified,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Create a new account. Returns access token + sets refresh cookie."""
    # Check for existing email (case-insensitive)
    existing = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email.lower(),
        display_name=body.display_name or body.email.split("@")[0],
        password_hash=hash_password(body.password),
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()   # populates user.id before commit
    await db.commit()
    await db.refresh(user)

    access  = create_token(user.id, "access")
    refresh = create_token(user.id, "refresh")
    _set_refresh_cookie(response, refresh)

    return TokenResponse(access_token=access, user=_build_token_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Verify credentials. Returns access token + sets refresh cookie."""
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()

    # Use verify_password even on None to prevent timing attacks that reveal
    # whether an email address is registered
    dummy_hash = "$2b$12$invalidhashpaddingtomakethisconstanttime00000000000000000"
    valid = verify_password(body.password, user.password_hash if user else dummy_hash)

    if not user or not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact support.",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    access  = create_token(user.id, "access")
    refresh = create_token(user.id, "refresh")
    _set_refresh_cookie(response, refresh)

    return TokenResponse(access_token=access, user=_build_token_response(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    """
    Swap a valid refresh cookie for a fresh access token + new refresh token.
    Called automatically by the frontend when a 401 is received.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired. Please log in again.",
    )
    if not refresh_token:
        raise _invalid

    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except JWTError:
        _clear_refresh_cookie(response)
        raise _invalid

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        _clear_refresh_cookie(response)
        raise _invalid

    access  = create_token(user.id, "access")
    new_refresh = create_token(user.id, "refresh")
    _set_refresh_cookie(response, new_refresh)

    return TokenResponse(access_token=access, user=_build_token_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """Clear the refresh cookie. Client should discard the access token."""
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserProfile)
async def me(current_user: User = Depends(get_current_active_user)):
    """Return the authenticated user's profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )
