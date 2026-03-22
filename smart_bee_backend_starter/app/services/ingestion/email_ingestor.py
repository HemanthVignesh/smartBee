"""Email Ingestor - Fetches and stores emails"""

from sqlalchemy.orm import Session
from app.services.ingestion.gmail_service import GmailService
from app.models.email import Email
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailIngestor:
    """Fetches emails from Gmail and stores them in database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gmail = GmailService()

    def fetch_and_store_unread(self, max_results: int = 10):
        """
        Fetch unread emails from Gmail and store in database
        Returns list of newly saved emails
        """
        try:
            emails = self.gmail.get_unread_emails(max_results=max_results)
            logger.info(f"Fetched {len(emails)} emails from Gmail")
            
            saved_emails = []

            for e in emails:
                # Check if email already exists
                exists = self.db.query(Email).filter_by(
                    message_id=e["message_id"]
                ).first()

                if exists:
                    logger.debug(f"Email {e['message_id']} already exists, skipping")
                    continue

                # Parse received_at date if possible
                received_at = datetime.utcnow()
                if e.get("received_at"):
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(e["received_at"])
                    except:
                        pass

                # Create new email
                new_email = Email(
                    message_id=e["message_id"],
                    sender=e["sender"],
                    subject=e["subject"],
                    body=e["body"],
                    received_at=received_at,
                    processed=False
                )

                self.db.add(new_email)
                saved_emails.append(new_email)
                logger.info(f"Added new email: {e['subject'][:50]}")

            # Commit all at once
            self.db.commit()
            logger.info(f"Saved {len(saved_emails)} new emails to database")
            
            return saved_emails
        
        except Exception as e:
            logger.error(f"Error in fetch_and_store_unread: {e}")
            self.db.rollback()
            raise