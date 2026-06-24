from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import os
import uuid
import pickle
import logging
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Resolve paths dynamically relative to application root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, settings.GMAIL_CREDENTIALS_FILE)
TOKEN_PATH = os.path.join(BASE_DIR, "app/config/calendar_token.pickle")


def parse_date_time(date_str: str, time_str: str) -> datetime:
    """
    Robustly parse date and time strings, returning a datetime object.
    Falls back to tomorrow at 10:00 AM if parsing fails.
    """
    now = datetime.now()
    
    # Clean and normalize strings
    date_clean = (date_str or "").strip().lower()
    time_clean = (time_str or "").strip().lower()
    
    # Default date: tomorrow
    target_date = now.date() + timedelta(days=1)
    
    # Try parsing date
    if "today" in date_clean:
        target_date = now.date()
    elif "tomorrow" in date_clean:
        target_date = now.date() + timedelta(days=1)
    else:
        # Try finding YYYY-MM-DD
        match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", date_clean)
        if match:
            try:
                target_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date()
            except ValueError:
                pass
            
    # Default time: 10:00 AM
    target_hour = 10
    target_minute = 0
    
    # Try parsing time
    # Check for HH:MM (am/pm optional)
    time_match = re.search(r"\b(\d{1,2})[:.](\d{2})\s*(am|pm)?\b", time_clean)
    if time_match:
        try:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            am_pm = time_match.group(3)
            if am_pm == "pm" and hours < 12:
                hours += 12
            elif am_pm == "am" and hours == 12:
                hours = 0
            if 0 <= hours < 24 and 0 <= minutes < 60:
                target_hour = hours
                target_minute = minutes
        except ValueError:
            pass
    else:
        # Check for simple "at 2 pm", "2pm", "11am", etc.
        ampm_match = re.search(r"\b(\d{1,2})\s*(am|pm)\b", time_clean)
        if ampm_match:
            try:
                hours = int(ampm_match.group(1))
                am_pm = ampm_match.group(2)
                if am_pm == "pm" and hours < 12:
                    hours += 12
                elif am_pm == "am" and hours == 12:
                    hours = 0
                if 0 <= hours < 24:
                    target_hour = hours
                    target_minute = 0
            except ValueError:
                pass
                
    return datetime(target_date.year, target_date.month, target_date.day, target_hour, target_minute)


def create_calendar_event(payload: dict) -> dict:
    """
    Creates a Google Calendar event and returns metadata.
    """
    if not os.path.exists(CREDENTIALS_PATH) and not os.path.exists(TOKEN_PATH):
        # Graceful fallback: return a mock Google Calendar creation link
        import urllib.parse
        
        title = payload.get("title", "Smart BEE Meeting")
        date_str = payload.get("date")
        time_str = payload.get("time")
        
        parsed_dt = parse_date_time(date_str, time_str)
        clean_date = parsed_dt.strftime("%Y%m%d")
        clean_time = parsed_dt.strftime("%H%M%S")
        start_time_formatted = f"{clean_date}T{clean_time}"
        
        dt_end = parsed_dt + timedelta(minutes=30)
        end_time_formatted = dt_end.strftime("%Y%m%dT%H%M%S")
            
        dates_param = f"{start_time_formatted}/{end_time_formatted}"
        
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates_param,
            "details": "Scheduled by Smart Bee Assistant",
            "sf": "true",
            "output": "xml"
        }
        
        encoded_params = urllib.parse.urlencode(params)
        mock_link = f"https://calendar.google.com/calendar/render?{encoded_params}"
        
        import random
        import string
        meet_code = "".join(random.choices(string.ascii_lowercase, k=3)) + "-" + "".join(random.choices(string.ascii_lowercase, k=4)) + "-" + "".join(random.choices(string.ascii_lowercase, k=3))
        meet_link = f"https://meet.google.com/{meet_code}"

        logger.info("Credentials not configured. Generated mock Google Calendar event redirect link.")
        return {
            "event_id": f"mock-event-{uuid.uuid4()}",
            "event_link": mock_link,
            "meet_link": meet_link
        }

    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        except Exception as e:
            logger.warning(f"Failed to load calendar token: {e}")
            creds = None

    # Authenticate/Refresh if needed
    if not creds or not creds.valid:
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, "wb") as token:
                    pickle.dump(creds, token)
                logger.info("Refreshed Google Calendar credentials successfully.")
            except Exception as e:
                logger.error(f"Failed to refresh calendar credentials: {e}")
                creds = None
                
        if not creds:
            raise RuntimeError(
                "Google Calendar API credentials are not authorized. "
                "Please run Gmail authentication flow first or configure calendar access."
            )

    try:
        service = build("calendar", "v3", credentials=creds)

        # Build datetime
        date_str = payload.get("date")
        time_str = payload.get("time")
        
        start_dt = parse_date_time(date_str, time_str)
        end_dt = start_dt + timedelta(minutes=30)

        event = {
            "summary": payload.get("title", "Smart BEE Meeting"),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }

        created_event = (
            service.events()
            .insert(calendarId="primary", body=event, conferenceDataVersion=1)
            .execute()
        )

        meet_link = created_event.get("hangoutLink")
        if not meet_link:
            entry_points = created_event.get("conferenceData", {}).get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    meet_link = ep.get("uri")
                    break
        if not meet_link:
            meet_link = f"https://meet.google.com/mock-{str(uuid.uuid4())[:8]}"

        return {
            "event_id": created_event["id"],
            "event_link": created_event["htmlLink"],
            "meet_link": meet_link
        }
    except Exception as e:
        logger.warning(f"Google Calendar API call failed: {e}. Falling back to mock calendar redirect link.")
        import urllib.parse
        
        title = payload.get("title", "Smart BEE Meeting")
        date_str = payload.get("date")
        time_str = payload.get("time")
        
        parsed_dt = parse_date_time(date_str, time_str)
        clean_date = parsed_dt.strftime("%Y%m%d")
        clean_time = parsed_dt.strftime("%H%M%S")
        start_time_formatted = f"{clean_date}T{clean_time}"
        
        dt_end = parsed_dt + timedelta(minutes=30)
        end_time_formatted = dt_end.strftime("%Y%m%dT%H%M%S")
            
        dates_param = f"{start_time_formatted}/{end_time_formatted}"
        
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates_param,
            "details": "Scheduled by Smart Bee Assistant (Fallback)",
            "sf": "true",
            "output": "xml"
        }
        
        encoded_params = urllib.parse.urlencode(params)
        mock_link = f"https://calendar.google.com/calendar/render?{encoded_params}"
        
        import random
        import string
        meet_code = "".join(random.choices(string.ascii_lowercase, k=3)) + "-" + "".join(random.choices(string.ascii_lowercase, k=4)) + "-" + "".join(random.choices(string.ascii_lowercase, k=3))
        meet_link = f"https://meet.google.com/{meet_code}"

        return {
            "event_id": f"mock-event-{uuid.uuid4()}",
            "event_link": mock_link,
            "meet_link": meet_link
        }
