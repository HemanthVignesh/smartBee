"""
SmartBee — SQLAlchemy ORM models
──────────────────────────────────
Each class maps to one database table.
Adding a new table = add a class here + create a migration (see migrations/).

Tables
──────
  email_logs      — every AI analysis decision, one row per email processed
  secure_settings — encrypted key-value store (API keys, runtime config)
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmailLog(Base):
    """
    Records every email that the AI brain processes.
    Replaces the old hand-rolled INSERT in api.py.
    """
    __tablename__ = "email_logs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    sender     = Column(String(320), nullable=False, index=True)   # max RFC 5321 email len
    subject    = Column(Text,        nullable=False)
    intent     = Column(String(64),  nullable=False, index=True)
    confidence = Column(Float,       nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return f"<EmailLog id={self.id} intent={self.intent!r} sender={self.sender!r}>"


class SecureSetting(Base):
    """
    Encrypted key-value store.
    Replaces the hand-rolled secure_settings table in security/keys.py.
    """
    __tablename__ = "secure_settings"

    key   = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<SecureSetting key={self.key!r}>"
