from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import os

import pickle

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Use absolute paths
BASE_DIR = "/Users/hemanthvignesh/Desktop/SmartBeee/smart_bee_backend_starter"
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")


def create_calendar_event(payload: dict) -> dict:
    """
    Creates a Google Calendar event and returns metadata.
    """

    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Authenticate if needed
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Build datetime
    start_dt = datetime.fromisoformat(
        f"{payload['date']}T{payload['time']}:00"
    )

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
    }

    created_event = (
        service.events()
        .insert(calendarId="primary", body=event)
        .execute()
    )

    return {
        "event_id": created_event["id"],
        "event_link": created_event["htmlLink"],
    }
