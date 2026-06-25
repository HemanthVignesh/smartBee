"""
SmartBee — FastAPI application entry point
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .brain import analyze_email
from .scheduler import create_calendar_event, create_reminder
from .gmail_service import fetch_emails, apply_label
from .database import get_db, init_db
from .utils.datetime_utils import now_iso
from .models.orm import EmailLog
from .models.schemas import (
    EmailRequest,
    BrainResponse,
    ActionRequest,
    StatusResponse,
)
from .config import settings
from .api.v1.settings import router as settings_router
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.trusted_host import TrustedHostMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware


# ─── Lifespan (replaces deprecated @app.on_event) ────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # creates tables if they don't exist
    yield
    # (add cleanup here if needed — close connection pools, etc.)


app = FastAPI(title="Smart Bee Brain API", version="1.0.0", lifespan=lifespan)


# ─── Middleware stack ─────────────────────────────────────────────────────────
#  Request flow:  SecurityHeaders → TrustedHost → RateLimit → CORS → route
#  (added in reverse — last added = outermost)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TrustedHostMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(settings_router)


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Smart Bee Backend Running", "env": settings.APP_ENV}


@app.get("/health")
def health():
    return {"status": "ok"}


# ─── Inbox (mock until real Gmail OAuth) ─────────────────────────────────────

@app.get("/emails")
def get_emails():
    return fetch_emails()


# ─── Brain ───────────────────────────────────────────────────────────────────

@app.post("/analyze-email", response_model=BrainResponse)
async def analyze(data: EmailRequest, db: AsyncSession = Depends(get_db)):
    result = analyze_email(
        subject=data.subject,
        body=data.body,
        sender=data.sender,
    )
    # Persist via SQLAlchemy — works with both SQLite and PostgreSQL
    db.add(EmailLog(
        sender=data.sender,
        subject=data.subject,
        intent=result["intent"],
        confidence=result["confidence"],
    ))
    # commit happens automatically when get_db() context exits
    return result


# ─── Actions ─────────────────────────────────────────────────────────────────

@app.post("/schedule", response_model=StatusResponse)
def schedule(action: ActionRequest):
    event = create_calendar_event(
        title="Meeting",
        date=action.meta.get("date"),
        time=action.meta.get("time"),
        meta=action.meta,
    )
    return {"status": "success", "message": "Event scheduled", "meta": event}


@app.post("/reminder", response_model=StatusResponse)
def reminder(action: ActionRequest):
    r = create_reminder(message="Reminder", remind_at=action.meta.get("date"))
    return {"status": "success", "message": "Reminder created", "meta": r}


@app.post("/label", response_model=StatusResponse)
def label(action: ActionRequest):
    apply_label(
        email_id=action.meta.get("email_id"),
        label=action.meta.get("label"),
    )
    return {"status": "success", "message": "Email labeled", "meta": action.meta}
