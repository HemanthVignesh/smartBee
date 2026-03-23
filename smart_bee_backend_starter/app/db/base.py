from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models for registration
from app.models.audit import AuditLog
from app.models.chat_history import ChatHistory
