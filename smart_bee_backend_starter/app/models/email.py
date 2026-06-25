"""
Email model — UPDATED: adds user_id FK so each email row is owned by one user.

Migration note:
  The existing `emails` table gains a `user_id` column.  The Alembic migration
  below handles this automatically.  If you're running a fresh DB the column
  is created by Base.metadata.create_all() at startup.

  For an existing DB with data, the migration sets user_id to NULL on old rows.
  You can assign them manually afterwards, or clear and re-sync:
      DELETE FROM emails;   -- then trigger a fresh Gmail sync per user.
"""

from sqlalchemy import Integer, Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, unique=True, nullable=True)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed = Column(Boolean, default=False)
    category = Column(String, default="primary", nullable=True)

    # ── Owner ────────────────────────────────────────────────────────────────
    # nullable=True so existing rows aren't immediately broken; tighten later.
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user = relationship("User", foreign_keys=[user_id])

    # ── Relationships ─────────────────────────────────────────────────────────
    decisions = relationship("Decision", back_populates="email")
    analysis = relationship("EmailAnalysis", back_populates="email", uselist=False)
