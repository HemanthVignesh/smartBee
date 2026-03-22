from pydantic import BaseModel
from typing import List, Dict, Any
from app.schemas.action import SuggestedActionResponse

class InsightResponse(BaseModel):
    email_id: str
    summary: str
    intent: str
    priority: str
    confidence: float
    entities: Dict[str, Any]
    actions: List[SuggestedActionResponse]
