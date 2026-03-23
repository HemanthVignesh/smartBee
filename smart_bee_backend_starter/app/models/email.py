from sqlalchemy import Integer, Column, String, Text, DateTime, Boolean
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

    decisions = relationship("Decision", back_populates="email")
    analysis = relationship("EmailAnalysis", back_populates="email", uselist=False)

