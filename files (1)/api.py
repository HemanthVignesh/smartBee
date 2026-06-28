"""
SmartBee — FastAPI application entry point
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.dependencies import get_current_active_user
from .brain import analyze_email
from .scheduler import create_calendar_event, create_reminder
from .gmail_service import fetch_emails, apply_label
from .database import get_db, init_db
from .models.orm import EmailLog, User
from .models.schemas import (
    EmailRequest,
    BrainResponse,
    ActionRequest,
    StatusResponse,
)
from .config import settings
from .api.v1.auth import router as auth_router
from .api.v1.settings import router as settings_router
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.trusted_host import TrustedHostMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Smart Bee Brain API", version="1.0.0", lifespan=lifespan)


# ─── Middleware stack ─────────────────────────────────────────────────────────
#  Request flow:  SecurityHeaders → TrustedHost → RateLimit → CORS → route

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,   # required for the httpOnly refresh cookie
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TrustedHostMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(settings_router)


# ─── Public routes (no auth required) ────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Smart Bee Backend Running", "env": settings.APP_ENV}


@app.get("/health")
def health():
    return {"status": "ok"}


# ─── Protected routes (require valid JWT) ─────────────────────────────────────
# Every route below depends on get_current_active_user.
# If the token is missing or invalid → automatic 401.

@app.get("/emails")
def get_emails(current_user: User = Depends(get_current_active_user)):
    return fetch_emails()


@app.post("/analyze-email", response_model=BrainResponse)
async def analyze(
    data: EmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = analyze_email(
        subject=data.subject,
        body=data.body,
        sender=data.sender,
    )
    db.add(EmailLog(
        user_id=current_user.id,
        sender=data.sender,
        subject=data.subject,
        intent=result["intent"],
        confidence=result["confidence"],
    ))
    return result


@app.post("/schedule", response_model=StatusResponse)
def schedule(
    action: ActionRequest,
    current_user: User = Depends(get_current_active_user),
):
    event = create_calendar_event(
        title="Meeting",
        date=action.meta.get("date"),
        time=action.meta.get("time"),
        meta=action.meta,
    )
    return {"status": "success", "message": "Event scheduled", "meta": event}


@app.post("/reminder", response_model=StatusResponse)
def reminder(
    action: ActionRequest,
    current_user: User = Depends(get_current_active_user),
):
    r = create_reminder(message="Reminder", remind_at=action.meta.get("date"))
    return {"status": "success", "message": "Reminder created", "meta": r}


@app.post("/label", response_model=StatusResponse)
def label(
    action: ActionRequest,
    current_user: User = Depends(get_current_active_user),
):
    apply_label(
        email_id=action.meta.get("email_id"),
        label=action.meta.get("label"),
    )
    return {"status": "success", "message": "Email labeled", "meta": action.meta}
