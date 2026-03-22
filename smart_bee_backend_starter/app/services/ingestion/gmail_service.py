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

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailService:
    """Gmail API Service for Smart BEE"""
    
    def __init__(
        self, 
        creds_path: str = "/Users/hemanthvignesh/Desktop/SmartBeee/smart_bee_backend_starter/credentials.json", 
        token_path: str = "/Users/hemanthvignesh/Desktop/SmartBeee/smart_bee_backend_starter/token.pickle"
    ):
        self.creds_path = creds_path
        self.token_path = token_path
        self.service = self._authenticate()

    def _authenticate(self):
        """Handle OAuth2 authentication with Gmail"""
        creds = None

        # Load saved token if exists
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, "rb") as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing Gmail credentials")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # If no valid credentials, log in
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

            # Save the credentials
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                with open(self.token_path, "wb") as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved credentials to {self.token_path}")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        return build("gmail", "v1", credentials=creds)

    def get_unread_emails(self, max_results: int = 10) -> List[Dict]:
        """
        Fetch unread emails from Gmail
        """
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
                "received_at": date
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

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        # Check for multipart
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                
                # Recursive check for nested parts
                if "parts" in part:
                    nested_body = self._get_email_body(part)
                    if nested_body:
                        return nested_body

        # If no plain text part found, try body directly
        body = payload.get("body", {}).get("data")
        if body:
            return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")

        return ""

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Gmail"""
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