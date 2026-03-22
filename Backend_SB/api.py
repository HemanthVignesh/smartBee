from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .brain import analyze_email
from .scheduler import create_calendar_event, create_reminder
from .gmail_service import fetch_emails, apply_label
from .database import init_db
from .utils.datetime_utils import now_iso
from .models.schemas import (
    EmailRequest,
    BrainResponse,
    ActionRequest,
    StatusResponse
)

import sqlite3
from .config import DATABASE_PATH


app = FastAPI(
    title="Smart Bee Brain API",
    version="1.0.0"
)

# -------------------------
# Middleware
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Startup
# -------------------------

@app.on_event("startup")
def startup():
    init_db()

# -------------------------
# Health Check
# -------------------------

@app.get("/")
def root():
    return {"status": "Smart Bee Backend Running"}

# -------------------------
# Inbox (Mock)
# -------------------------

@app.get("/emails")
def get_emails():
    return fetch_emails()

# -------------------------
# Brain Endpoint
# -------------------------

@app.post("/analyze-email", response_model=BrainResponse)
def analyze(data: EmailRequest):
    result = analyze_email(
        subject=data.subject,
        body=data.body,
        sender=data.sender
    )

    # Log decision
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO email_logs (sender, subject, intent, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
        (data.sender, data.subject, result["intent"], result["confidence"], now_iso())
    )
    conn.commit()
    conn.close()

    return result

# -------------------------
# Actions
# -------------------------

@app.post("/schedule", response_model=StatusResponse)
def schedule(action: ActionRequest):
    event = create_calendar_event(
        title="Meeting",
        date=action.meta.get("date"),
        time=action.meta.get("time"),
        meta=action.meta
    )
    return {
        "status": "success",
        "message": "Event scheduled",
        "meta": event
    }


@app.post("/reminder", response_model=StatusResponse)
def reminder(action: ActionRequest):
    reminder = create_reminder(
        message="Reminder",
        remind_at=action.meta.get("date")
    )
    return {
        "status": "success",
        "message": "Reminder created",
        "meta": reminder
    }


@app.post("/label", response_model=StatusResponse)
def label(action: ActionRequest):
    apply_label(
        email_id=action.meta.get("email_id"),
        label=action.meta.get("label")
    )
    return {
        "status": "success",
        "message": "Email labeled",
        "meta": action.meta
    }
