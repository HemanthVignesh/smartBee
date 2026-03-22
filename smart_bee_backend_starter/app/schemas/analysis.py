from pydantic import BaseModel
from typing import Dict

class AnalysisResponse(BaseModel):
    email_id: str
    intent: str
    priority: str
    confidence: float
    summary: str
    entities: Dict
