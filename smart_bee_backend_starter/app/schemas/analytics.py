from pydantic import BaseModel
from typing import List, Dict

class AnalyticsStats(BaseModel):
    total_emails: int
    processed_emails: int
    actions_count: int
    time_saved_hours: float
    recent_activity: List[Dict]

class ProductivityTrend(BaseModel):
    label: str
    value: float
    is_positive: bool
