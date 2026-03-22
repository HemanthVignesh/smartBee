"""
Gmail Service Module (Passive)

NOTE:
- This file does NOT auto-fetch emails
- It only exposes reusable functions
- Google API integration can be added later
"""

from typing import List, Dict
from datetime import datetime, timezone


def fetch_emails(limit: int = 10) -> List[Dict]:
    """
    Dummy email fetcher (prototype).
    """

    emails = [
        {
            "id": "email_1",
            "sender": "manager@company.com",
            "subject": "Meeting tomorrow at 10 AM",
            "body": "Let's discuss the project updates.",
            "timestamp": datetime(2026, 1, 28, 9, 0, tzinfo=timezone.utc).isoformat()
        },
        {
            "id": "email_2",
            "sender": "hr@company.com",
            "subject": "Deadline for document submission",
            "body": "Please submit the documents before Friday.",
            "timestamp": datetime(2026, 1, 27, 18, 30, tzinfo=timezone.utc).isoformat()
        }
    ]

    return emails[:limit]


def apply_label(email_id: str, label: str) -> bool:
    """
    Applies a label to an email (stub).
    """
    return True


def mark_as_read(email_id: str) -> bool:
    """
    Marks an email as read (stub).
    """
    return True
