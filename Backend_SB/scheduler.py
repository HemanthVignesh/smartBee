"""
Scheduler Service (Logic Only)

Handles:
- Calendar event creation (stub)
- Reminder scheduling (stub)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from .config import DEFAULT_REMINDER_OFFSET_MINUTES


def create_calendar_event(
    title: str,
    date: str,
    time: str,
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Creates a calendar event (prototype).
    """

    return {
        "status": "scheduled",
        "event": {
            "title": title,
            "date": date,
            "time": time,
            "meta": meta or {}
        }
    }


def create_reminder(
    message: str,
    remind_at: str = None
) -> Dict[str, Any]:
    """
    Creates a reminder with timezone-aware UTC time.
    """

    if not remind_at:
        remind_time = datetime.now(timezone.utc) + timedelta(
            minutes=DEFAULT_REMINDER_OFFSET_MINUTES
        )
        remind_at = remind_time.isoformat()

    return {
        "status": "reminder_set",
        "message": message,
        "remind_at": remind_at
    }
