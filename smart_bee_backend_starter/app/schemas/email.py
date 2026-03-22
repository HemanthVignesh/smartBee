from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmailResponse(BaseModel):
    id: str
    message_id: Optional[str]
    sender: str
    subject: str | None
    body: str | None
    received_at: datetime
    processed: bool

    model_config = {
        "from_attributes": True
    }

