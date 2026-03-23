from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text
from datetime import datetime
import uuid
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String) # e.g., "action", "email", "login"
    entity_id = Column(String)
    action = Column(String) # e.g., "execute", "delete", "create"
    user_id = Column(String, nullable=True)
    status = Column(String) # "success", "failure"
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
