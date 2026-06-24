from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.action import SuggestedActionResponse

class InsightResponse(BaseModel):
    email_id: str
    sender: str
    subject: Optional[str]
    received_at: datetime
    category: Optional[str]
    summary: str
    intent: str
    priority: str
    confidence: float
    entities: Dict[str, Any]
    actions: List[SuggestedActionResponse]
    rationale: Optional[str] = None
