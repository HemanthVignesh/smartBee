from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.base import Base

class SuggestedAction(Base):
    __tablename__ = "suggested_actions"

    id = Column(String, primary_key=True)
    decision_id = Column(String, ForeignKey("decisions.id"))
    action_type = Column(String)
    payload = Column(JSON)
    status = Column(String, default="pending") # pending, scheduled, executed, failed, rejected
    scheduled_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    execution_metadata = Column(JSON, nullable=True)

    decision = relationship("Decision", back_populates="actions")

    @property
    def action_id(self) -> str:
        return self.id
