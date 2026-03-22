from pydantic import BaseModel
from typing import Optional, Dict, Any


class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: str


class BrainResponse(BaseModel):
    intent: str
    confidence: float
    reason: str
    suggested_action: str
    requires_confirmation: bool
    meta: Dict[str, Any]


class ActionRequest(BaseModel):
    meta: Dict[str, Any]


class StatusResponse(BaseModel):
    status: str
    message: str
    meta: Optional[Dict[str, Any]] = None
