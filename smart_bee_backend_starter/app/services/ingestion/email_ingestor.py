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

                # 1. Create new email
                new_email = Email(
                    message_id=e["message_id"],
                    sender=e["sender"],
                    subject=e["subject"],
                    body=e["body"],
                    received_at=received_at,
                    processed=False
                )
                self.db.add(new_email)
                self.db.flush() # Get the UUID

                # 2. Run AI Analysis Pipeline
                try:
                    from app.services.ai_engine.intent_detector import detect_intent
                    from app.services.ai_engine.entity_extractor import extract_entities
                    from app.services.ai_engine.priority_scorer import score_priority
                    from app.services.ai_engine.summarizer import EmailSummarizer
                    from app.models.analysis import EmailAnalysis
                    from app.models.decision import Decision
                    from app.models.action import SuggestedAction
                    import uuid

                    # Detect intent and entities
                    intent_data = detect_intent(new_email.subject, new_email.body)
                    entities = extract_entities(new_email.subject, new_email.body)
                    priority = score_priority(new_email.body, intent_data.get("intent", "general"))
                    
                    summarizer = EmailSummarizer()
                    summary = summarizer.summarize(new_email.body)

                    # Store Analysis
                    analysis = EmailAnalysis(
                        email_id=new_email.id,
                        intent=intent_data.get("intent", "general"),
                        priority=priority,
                        confidence=intent_data.get("confidence", 0.7),
                        summary=summary,
                        entities=entities
                    )
                    self.db.add(analysis)

                    # Create Decision
                    decision = Decision(
                        email_id=new_email.id,
                        decision_type=intent_data.get("intent", "general"),
                        rationale=intent_data.get("reasoning", "Automated analysis"),
                        auto_executable=False
                    )
                    self.db.add(decision)
                    self.db.flush()

                    # Create Suggested Action based on intent
                    if intent_data.get("intent") == "meeting_request":
                        # Attempt to extract meeting details from entities
                        dates = entities.get("dates", [])
                        times = entities.get("times", [])
                        
                        action_payload = {
                            "title": f"Meeting with {new_email.sender}",
                            "date": dates[0] if dates else datetime.now().strftime("%Y-%m-%d"),
                            "time": times[0] if times else "10:00"
                        }
                        
                        action = SuggestedAction(
                            id=str(uuid.uuid4()),
                            decision_id=decision.id,
                            action_type="create_calendar_event",
                            payload=action_payload,
                            status="pending"
                        )
                        self.db.add(action)
                    
                    elif intent_data.get("intent") in ["general", "question"]:
                        from app.services.ai_engine.reply_generator import generate_replies
                        reply = generate_replies(new_email.body, intent_data.get("intent"), priority, entities)
                        
                        action = SuggestedAction(
                            id=str(uuid.uuid4()),
                            decision_id=decision.id,
                            action_type="generate_reply",
                            payload={"replies": [reply]},
                            status="pending"
                        )
                        self.db.add(action)

                except Exception as ai_err:
                    logger.error(f"AI Analysis failed for email {new_email.id}: {ai_err}")

                saved_emails.append(new_email)
                logger.info(f"Added new email and analysis for: {e['subject'][:50]}")

            # Commit all at once
            self.db.commit()
            logger.info(f"Saved {len(saved_emails)} new emails to database")
            
            return saved_emails
        
        except Exception as e:
            logger.error(f"Error in fetch_and_store_unread: {e}")
            self.db.rollback()
            raise