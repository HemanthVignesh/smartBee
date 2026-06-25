"""
User model — stores one row per authenticated Google account.
All other tables (emails, analysis, decisions, actions, chat_history,
audit_logs) gain a user_id FK so data is fully isolated per user.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # ── Google OAuth fields ──────────────────────────────────────────────────
    google_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    picture = Column(Text, nullable=True)         # Profile photo URL from Google

    # ── App-level flags ──────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)   # Inherits from Google's verification

    # ── Per-user Gmail tokens (encrypted at rest — see auth/token_store.py) ──
    gmail_token_json = Column(Text, nullable=True)  # JSON-serialised google OAuth token

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
