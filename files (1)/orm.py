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
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    Registered SmartBee users.
    Passwords are stored as bcrypt hashes — never plain text.
    """
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(320), nullable=False, unique=True, index=True)
    display_name  = Column(String(128), nullable=True)
    password_hash = Column(String(256), nullable=False)
    is_active     = Column(Boolean, nullable=False, default=True)
    is_verified   = Column(Boolean, nullable=False, default=False)
    created_at    = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=func.now(),
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship — each user owns their email logs
    email_logs = relationship("EmailLog", back_populates="user", lazy="select")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class EmailLog(Base):
    """
    Records every email that the AI brain processes.
    Replaces the old hand-rolled INSERT in api.py.
    """
    __tablename__ = "email_logs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    # FK to the user who owns this log — nullable so old rows without a user still load
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    sender     = Column(String(320), nullable=False, index=True)
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

    user = relationship("User", back_populates="email_logs")

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
