from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class EmailAnalysis(Base):
    __tablename__ = "email_analysis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = Column(String, ForeignKey("emails.id"))
    intent = Column(String)
    priority = Column(String)
    confidence = Column(Float)
    summary = Column(Text)
    entities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("Email", back_populates="analysis")
