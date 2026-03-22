from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    feedback_type: str  # "accepted" or "rejected"
