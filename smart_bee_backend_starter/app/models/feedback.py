from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from datetime import datetime
import uuid

from app.db.base import Base

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id = Column(String, ForeignKey("suggested_actions.id"))
    feedback_type = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
