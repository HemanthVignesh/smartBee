from pydantic import BaseModel
from typing import Optional, Dict, Any

class SuggestedActionResponse(BaseModel):
    action_id: str
    action_type: str
    payload: Dict[str, Any]
    status: str
    execution_metadata: Optional[Dict[str, Any]] = None
