from pydantic import BaseModel
from typing import Optional, Dict, Any

class FeedbackRequest(BaseModel):
    feedback_type: str  # "accepted" or "rejected"
    custom_payload: Optional[Dict[str, Any]] = None
