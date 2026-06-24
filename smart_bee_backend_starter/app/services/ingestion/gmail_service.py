"""Gmail Service - Complete Implementation"""

import base64
import os
import pickle
from email.mime.text import MIMEText
from typing import List, Dict, Optional
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


from html.parser import HTMLParser
import re

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.convert_charrefs = True
        self.text = []
        self.ignore_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in ["style", "script", "head"]:
            self.ignore_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ["style", "script", "head"]:
            if tag in self.ignore_stack:
                self.ignore_stack.remove(tag)

    def handle_data(self, d):
        if not self.ignore_stack:
            self.text.append(d)

    def get_data(self):
        content = ''.join(self.text)
        lines = [line.strip() for line in content.split('\n')]
        return '\n'.join([line for line in lines if line])

def strip_html(html_content: str) -> str:
    try:
        s = HTMLStripper()
        s.feed(html_content)
        return s.get_data()
    except Exception as e:
        logger.warning(f"Failed to strip HTML: {e}")
        return html_content


class GmailService:
    """Gmail API Service for Smart BEE"""
    
    def __init__(
        self, 
        creds_path: Optional[str] = None, 
        token_path: Optional[str] = None
    ):
        # Resolve paths dynamically relative to application root
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        
        self.creds_path = creds_path or os.path.join(base_dir, settings.GMAIL_CREDENTIALS_FILE)
        self.token_path = token_path or os.path.join(base_dir, settings.GMAIL_TOKEN_FILE)
        self.mock_mode = False
        try:
            self.service = self._authenticate()
        except Exception as e:
            logger.warning(f"Gmail initialization failed. Switching to mock mode: {e}")
            self.mock_mode = True
            self.service = None

    def _authenticate(self):
        """Handle OAuth2 authentication with Gmail.
        Supports both pickle and JSON token storage formats.
        """
        import json as _json
        from google.oauth2.credentials import Credentials as Creds

        creds = None

        # Validate credentials file is non-empty before parsing
        if os.path.exists(self.creds_path):
            if os.path.getsize(self.creds_path) == 0:
                raise ValueError(
                    f"credentials.json at '{self.creds_path}' is empty. "
                    "Please download a valid OAuth2 credentials file from Google Cloud Console."
                )
        
        # ── Token loading: try pickle first, then JSON ──────────────────────
        # Also check for a sibling .json token file (e.g. token.json)
        json_token_path = os.path.splitext(self.token_path)[0] + ".json"

        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing Gmail credentials from pickle token")
            except Exception as e:
                logger.warning(f"Failed to load pickle token: {e}")

        if not creds and os.path.exists(json_token_path):
            try:
                creds = Creds.from_authorized_user_file(json_token_path, SCOPES)
                logger.info("Loaded existing Gmail credentials from JSON token")
            except Exception as e:
                logger.warning(f"Failed to load JSON token: {e}")

        # ── Refresh or re-authorize if needed ───────────────────────────────
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Gmail credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.creds_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.creds_path}\n"
                        "Please download OAuth2 credentials from Google Cloud Console"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth2 flow")

            # Save the credentials (pickle format)
            try:
                os.makedirs(os.path.dirname(self.token_path) or ".", exist_ok=True)
                with open(self.token_path, "wb") as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved credentials to {self.token_path}")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        return build("gmail", "v1", credentials=creds)


    def get_unread_emails(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch unread emails from Gmail.
        Returns an empty list when running in mock mode (no credentials configured).
        """
        if self.mock_mode:
            logger.info("GmailService running in mock mode: no credentials configured, returning empty list.")
            return []
        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me", 
                    labelIds=["INBOX"], 
                    q="is:unread", 
                    maxResults=max_results
                )
                .execute()
            )

            messages = results.get("messages", [])
            
            if not messages:
                logger.info("No unread messages found")
                return []

            logger.info(f"Found {len(messages)} unread messages")
            
            emails = []
            for msg in messages:
                try:
                    email_data = self._get_email_details(msg["id"])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Failed to fetch email {msg['id']}: {e}")
                    continue

            return emails
        
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Error fetching unread emails: {e}")
            return []

    def _get_email_details(self, msg_id: str) -> Optional[Dict]:
        """Get detailed information about a specific email"""
        try:
            msg_data = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )

            headers = msg_data["payload"]["headers"]
            subject = self._get_header(headers, "Subject")
            sender = self._get_header(headers, "From")
            date = self._get_header(headers, "Date")
            body = self._get_email_body(msg_data["payload"])

            return {
                "message_id": msg_id,
                "sender": sender,
                "subject": subject or "(No Subject)",
                "body": body,
                "received_at": date,
                "label_ids": msg_data.get("labelIds", [])
            }
        
        except Exception as e:
            logger.error(f"Error getting email details for {msg_id}: {e}")
            return None

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract header value by name"""
        for h in headers:
            if h["name"] == name:
                return h["value"]
        return ""

    def _find_body_by_mimetype(self, payload: Dict, mimetype: str) -> Optional[str]:
        """Recursively find content matching mimetype in the Gmail payload."""
        if payload.get("mimeType") == mimetype:
            data = payload.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        
        if "parts" in payload:
            for part in payload["parts"]:
                found = self._find_body_by_mimetype(part, mimetype)
                if found:
                    return found
        return None

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload, resolving HTML to plain text if needed."""
        # Try to find text/plain first
        plain_text = self._find_body_by_mimetype(payload, "text/plain")
        if plain_text:
            return plain_text

        # Try to find text/html
        html_text = self._find_body_by_mimetype(payload, "text/html")
        if html_text:
            return strip_html(html_text)

        # Fallback: check body directly if present
        body_data = payload.get("body", {}).get("data")
        if body_data:
            decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
            # If it looks like HTML, strip it
            if re.search(r"<[a-zA-Z/!?][^>]*>", decoded) or "html" in decoded.lower():
                return strip_html(decoded)
            return decoded

        return ""

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Gmail"""
        to = "hemanthvignesh27@gmail.com"
        if self.mock_mode:
            logger.info(f"Mocking send email to {to}: Subject: {subject}")
            return True
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def get_profile(self) -> Optional[Dict]:
        """Get Gmail profile information"""
        if self.mock_mode:
            return {
                'email': None,
                'connected': False,
                'message': 'Gmail not configured. Please set up OAuth2 credentials.'
            }

        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            }
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return None