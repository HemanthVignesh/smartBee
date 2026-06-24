from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalyticsStats(BaseModel):
    total_emails: int
    processed_emails: int
    actions_count: int
    time_saved_hours: float
    recent_activity: List[Dict]
    emails_per_week: Optional[List[Dict]] = None
    time_saved_trend: Optional[List[Dict]] = None

class ProductivityTrend(BaseModel):
    label: str
    value: float
    is_positive: bool
