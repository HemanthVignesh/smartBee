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

                # 1. Map category from Gmail labelIds first to mimic Gmail categorization
                category = None
                label_ids = e.get("label_ids", [])
                if label_ids:
                    for label in label_ids:
                        if label == "CATEGORY_PERSONAL":
                            category = "primary"
                            break
                        elif label == "CATEGORY_PROMOTIONS":
                            category = "promotions"
                            break
                        elif label == "CATEGORY_SOCIAL":
                            category = "social"
                            break
                        elif label == "CATEGORY_UPDATES":
                            category = "updates"
                            break
                        elif label == "CATEGORY_FORUMS":
                            category = "forums"
                            break
                
                # If no Gmail category label is found, fall back to AI categorization
                if not category:
                    try:
                        from app.services.ai_engine.categorizer import categorize_email
                        category = categorize_email(e["subject"], e["body"], e["sender"])
                    except Exception as cat_err:
                        logger.error(f"Category detection failed for email message {e['message_id']}: {cat_err}")
                        category = "primary"

                is_primary = (category == "primary")
                intent_data = {}
                entities = {}
                priority = "medium"
                summary = ""

                # 2. Run AI Analysis Pipeline in-memory ONLY for Primary emails
                if is_primary:
                    try:
                        from app.services.ai_engine.intent_detector import detect_intent
                        from app.services.ai_engine.entity_extractor import extract_entities
                        from app.services.ai_engine.priority_scorer import score_priority
                        from app.services.ai_engine.summarizer import EmailSummarizer

                        # Detect intent, entities and category using in-memory email data
                        intent_data = detect_intent(e["subject"], e["body"])
                        entities = extract_entities(e["subject"], e["body"])
                        priority = score_priority(e["body"], intent_data.get("intent", "general"))
                        
                        summarizer = EmailSummarizer()
                        summary = summarizer.summarize(e["body"])
                    except Exception as ai_err:
                        logger.error(f"AI Analysis failed for email message {e['message_id']}: {ai_err}")

                # 3. Write to DB: Only write analysis/decisions/actions for Primary category emails
                try:
                    # Create and store email
                    new_email = Email(
                        message_id=e["message_id"],
                        sender=e["sender"],
                        subject=e["subject"],
                        body=e["body"],
                        received_at=received_at,
                        processed=False,
                        category=category
                    )
                    self.db.add(new_email)
                    self.db.flush() # Get the UUID

                    if is_primary:
                        from app.models.analysis import EmailAnalysis
                        from app.models.decision import Decision
                        from app.models.action import SuggestedAction
                        import uuid

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

                        # Create Suggested Actions based on intent and needs_reply
                        needs_reply = intent_data.get("needs_reply", False)
                        
                        if intent_data.get("intent") == "meeting_request":
                            # Attempt to extract meeting details from entities
                            dates = entities.get("dates", [])
                            times = entities.get("times", [])
                            
                            action_payload = {
                                "title": f"Meeting with {new_email.sender}",
                                "date": dates[0] if dates else datetime.now().strftime("%Y-%m-%d"),
                                "time": times[0] if times else "10:00"
                            }
                            
                            calendar_action = SuggestedAction(
                                id=str(uuid.uuid4()),
                                decision_id=decision.id,
                                action_type="create_calendar_event",
                                payload=action_payload,
                                status="pending"
                            )
                            self.db.add(calendar_action)
                        
                        if needs_reply:
                            from app.services.ai_engine.reply_generator import generate_replies
                            reply = generate_replies(e["body"], intent_data.get("intent"), priority, entities)
                            
                            reply_action = SuggestedAction(
                                id=str(uuid.uuid4()),
                                decision_id=decision.id,
                                action_type="generate_reply",
                                payload={
                                    "replies": [reply],
                                    "to": "hemanthvignesh27@gmail.com",
                                    "subject": f"Re: {new_email.subject or 'Inquiry'}"
                                },
                                status="pending"
                            )
                            self.db.add(reply_action)

                    self.db.commit()
                    saved_emails.append(new_email)
                    logger.info(f"Added and committed new email for: {e['subject'][:50]}")
                except Exception as commit_err:
                    logger.error(f"Commit failed for email {e['message_id']}: {commit_err}")
                    self.db.rollback()

            logger.info(f"Progressive ingestion complete: saved {len(saved_emails)} new emails to database")
            return saved_emails
        
        except Exception as e:
            logger.error(f"Error in fetch_and_store_unread: {e}")
            self.db.rollback()
            raise