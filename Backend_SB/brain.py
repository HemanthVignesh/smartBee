"""
Smart Bee – Brain Module
-----------------------
Responsibilities:
- Understand email content
- Detect user intent
- Assign confidence score
- Explain reasoning
- Suggest next action

This module is UI-agnostic and API-ready.
"""

import re
from typing import Dict, Any


# -------------------------
# Utility Functions
# -------------------------

def _extract_date(text: str):
    """
    Extracts a simple date pattern from text (prototype-level).
    """
    date_patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",     # 12/01/2026
        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",     # 12-01-2026
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()

    return None


def _extract_time(text: str):
    """
    Extracts simple time patterns like '10 AM', '14:30'
    """
    time_patterns = [
        r"\b\d{1,2}:\d{2}\b",              # 14:30
        r"\b\d{1,2}\s?(am|pm)\b",          # 10 AM / 10 pm
    ]

    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group()

    return None


# -------------------------
# Core Brain Function
# -------------------------

def analyze_email(subject: str, body: str, sender: str) -> Dict[str, Any]:
    """
    Main decision-making function.
    Input: Raw email data
    Output: Structured AI decision (JSON-friendly)
    """

    text = f"{subject} {body}".lower()

    date = _extract_date(text)
    time = _extract_time(text)

    # -------------------------
    # Intent: Schedule Meeting
    # -------------------------
    if any(keyword in text for keyword in ["meeting", "call", "discussion", "zoom"]):
        confidence = 0.9 if date or time else 0.75

        return {
            "intent": "schedule_meeting",
            "confidence": confidence,
            "reason": "Meeting-related keywords detected in the email",
            "suggested_action": "Create calendar event",
            "requires_confirmation": True,
            "meta": {
                "date": date,
                "time": time,
                "sender": sender
            }
        }

    # -------------------------
    # Intent: Set Reminder
    # -------------------------
    if any(keyword in text for keyword in ["remind", "deadline", "due", "follow up"]):
        confidence = 0.85 if date else 0.7

        return {
            "intent": "set_reminder",
            "confidence": confidence,
            "reason": "Deadline or reminder-related keywords found",
            "suggested_action": "Set reminder",
            "requires_confirmation": True,
            "meta": {
                "date": date,
                "sender": sender
            }
        }

    # -------------------------
    # Intent: Categorize / Label
    # -------------------------
    if any(keyword in text for keyword in ["invoice", "payment", "bill", "receipt"]):
        return {
            "intent": "label_email",
            "confidence": 0.8,
            "reason": "Financial keywords detected",
            "suggested_action": "Label as Finance",
            "requires_confirmation": False,
            "meta": {
                "label": "Finance"
            }
        }

    # -------------------------
    # Intent: Informational Only
    # -------------------------
    if any(keyword in text for keyword in ["information", "update", "notice", "announcement"]):
        return {
            "intent": "informational",
            "confidence": 0.7,
            "reason": "Email appears informational with no required action",
            "suggested_action": "Mark as read",
            "requires_confirmation": False,
            "meta": {}
        }

    # -------------------------
    # Default: No Action
    # -------------------------
    return {
        "intent": "no_action",
        "confidence": 0.4,
        "reason": "No actionable intent detected",
        "suggested_action": "Ignore",
        "requires_confirmation": False,
        "meta": {}
    }
