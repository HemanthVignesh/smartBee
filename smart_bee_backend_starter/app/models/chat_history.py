from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from datetime import datetime
import uuid
from app.db.base import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True)
    role = Column(String) # "user", "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
