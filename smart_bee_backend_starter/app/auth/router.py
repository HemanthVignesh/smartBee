"""
auth/router.py — Google OAuth 2.0 + JWT session endpoints.

Flow:
  1.  GET  /api/v1/auth/google/login
        → Redirect browser to Google's consent screen.

  2.  GET  /api/v1/auth/google/callback?code=…&state=…
        → Exchange code for tokens, upsert User row, issue SmartBee JWT.
        → Redirect to frontend with token in query-string (or JSON in dev).

  3.  GET  /api/v1/auth/me
        → Return current user's profile (requires Bearer token).

  4.  POST /api/v1/auth/logout
        → Client-side only; endpoint exists for audit logging.

  5.  DELETE /api/v1/auth/account
        → Soft-delete (deactivate) the authenticated user.
"""

import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.auth.jwt import create_access_token
from app.core.config import settings
from app.models.user import User
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Google OAuth 2.0 constants ───────────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    # Gmail scopes — kept here so the same OAuth flow also authorises Gmail
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    # Calendar scope
    "https://www.googleapis.com/auth/calendar",
]


# ── Pydantic response schemas ─────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ── 1. Kick off Google OAuth flow ────────────────────────────────────────────

@router.get("/google/login")
def google_login():
    """
    Redirect the user to Google's OAuth consent screen.
    The redirect_uri must match exactly what is registered in Google Cloud Console.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.",
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",      # request refresh token
        "prompt": "consent",           # always show consent to get refresh_token
        "include_granted_scopes": "true",
    }

    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=url)


# ── 2. OAuth callback — exchange code → tokens → upsert user → JWT ───────────

@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Google redirects here with ?code=…  We exchange the code for
    Google tokens, fetch the user profile, upsert the User row, and
    issue a SmartBee JWT.  The browser is then sent to the frontend
    with the token embedded in the URL fragment (#token=…) so it
    never appears in server logs or the referrer header.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured.")

    # ── Step A: Exchange authorisation code for Google tokens ────────────────
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        logger.error(f"Google token exchange failed: {token_response.text}")
        raise HTTPException(
            status_code=400,
            detail="Failed to exchange authorisation code with Google.",
        )

    google_tokens = token_response.json()
    access_token_google = google_tokens.get("access_token")

    # ── Step B: Fetch user's profile from Google ─────────────────────────────
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token_google}"},
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch profile from Google.")

    userinfo = userinfo_response.json()
    google_id = userinfo.get("sub")
    email = userinfo.get("email")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Incomplete profile from Google.")

    # ── Step C: Upsert User row ───────────────────────────────────────────────
    user = db.query(User).filter(User.google_id == google_id).first()

    if user is None:
        # First login — create a new account
        user = User(
            google_id=google_id,
            email=email,
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            is_active=True,
            is_verified=userinfo.get("email_verified", True),
            gmail_token_json=json.dumps(google_tokens),
        )
        db.add(user)
        logger.info(f"New user registered: {email}")
    else:
        # Returning user — refresh tokens and profile
        user.name = userinfo.get("name", user.name)
        user.picture = userinfo.get("picture", user.picture)
        user.last_login = datetime.now(timezone.utc)
        # Only overwrite the stored Gmail token if Google returned a refresh_token
        if google_tokens.get("refresh_token"):
            user.gmail_token_json = json.dumps(google_tokens)
        logger.info(f"Existing user logged in: {email}")

    db.commit()
    db.refresh(user)

    # ── Step D: Issue SmartBee JWT ────────────────────────────────────────────
    smartbee_token = create_access_token(user_id=user.id, email=user.email)

    # Audit
    log_action(db, "auth", user.id, "google_login", "success", user_id=user.id)

    # ── Step E: Redirect browser to frontend with token in URL fragment ───────
    # The # fragment is never sent to the server, so the token stays client-side.
    frontend_url = settings.FRONTEND_URL
    redirect_url = f"{frontend_url}/auth/callback#token={smartbee_token}"
    return RedirectResponse(url=redirect_url)


# ── 3. Dev-only: token exchange via JSON (no browser redirect) ────────────────

@router.post("/google/token")
async def exchange_google_token_json(
    body: dict,
    db: Session = Depends(get_db),
):
    """
    Alternative callback for SPAs that handle the OAuth exchange client-side
    via the Google Identity Services JS library.  The client sends
    { "code": "…", "redirect_uri": "…" } and receives a JSON token response.
    """
    code = body.get("code")
    redirect_uri = body.get("redirect_uri", settings.GOOGLE_REDIRECT_URI)

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code'.")

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Google token exchange failed.")

    google_tokens = token_response.json()

    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
        )

    userinfo = userinfo_resp.json()
    google_id = userinfo.get("sub")
    email = userinfo.get("email")

    user = db.query(User).filter(User.google_id == google_id).first()
    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            gmail_token_json=json.dumps(google_tokens),
        )
        db.add(user)
    else:
        user.last_login = datetime.now(timezone.utc)
        if google_tokens.get("refresh_token"):
            user.gmail_token_json = json.dumps(google_tokens)

    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    log_action(db, "auth", user.id, "token_exchange", "success", user_id=user.id)

    return TokenResponse(
        access_token=token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


# ── 4. /me — authenticated user profile ──────────────────────────────────────

@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


# ── 5. Logout (audit trail only — JWT invalidation is client-side) ────────────

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stateless JWTs can't be server-side invalidated without a denylist.
    The client must delete the token from storage.  This endpoint exists
    so the event is captured in the audit log and for future denylist support.
    """
    log_action(db, "auth", current_user.id, "logout", "success", user_id=current_user.id)
    return {"message": "Logged out. Please delete your token client-side."}


# ── 6. Delete account (soft deactivate) ─────────────────────────────────────

@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete the authenticated user's account."""
    current_user.is_active = False
    db.commit()
    log_action(db, "auth", current_user.id, "delete_account", "success", user_id=current_user.id)
    return {"message": "Account deactivated. Contact support to restore it."}
