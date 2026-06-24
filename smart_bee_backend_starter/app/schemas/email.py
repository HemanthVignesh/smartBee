from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.schemas.action import SuggestedActionResponse

class EmailAnalysisSchema(BaseModel):
    id: str
    intent: str
    priority: str
    confidence: float
    summary: str
    entities: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DecisionSchema(BaseModel):
    id: str
    decision_type: str
    rationale: str
    auto_executable: bool
    created_at: datetime
    actions: List[SuggestedActionResponse] = []

    class Config:
        from_attributes = True

class EmailResponse(BaseModel):
    id: str
    message_id: Optional[str]
    sender: str
    subject: str | None
    body: str | None
    received_at: datetime
    processed: bool
    category: Optional[str] = "primary"
    analysis: Optional[EmailAnalysisSchema] = None
    decisions: List[DecisionSchema] = []

    model_config = {
        "from_attributes": True
    }

