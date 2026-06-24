import time
import threading
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.services.executors.calendar_executor import create_calendar_event
from app.services.ingestion.gmail_service import GmailService
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# How often (in seconds) to fetch new emails from Gmail
GMAIL_POLL_INTERVAL_SECONDS = 300  # every 5 minutes

def _poll_gmail():
    """Fetch new emails from Gmail and run them through the AI pipeline."""
    db = SessionLocal()
    try:
        from app.services.ingestion.email_ingestor import EmailIngestor
        ingestor = EmailIngestor(db)
        if ingestor.gmail.mock_mode:
            return  # Gmail not configured; skip silently
        saved = ingestor.fetch_and_store_unread(max_results=20)
        if saved:
            logger.info(f"Scheduler: fetched and processed {len(saved)} new email(s) from Gmail.")
    except Exception as e:
        logger.error(f"Scheduler Gmail poll error: {e}")
    finally:
        db.close()


def run_scheduler():
    """
    Background loop that:
      1. Executes any due scheduled actions (emails / calendar events)
      2. Polls Gmail for new emails every GMAIL_POLL_INTERVAL_SECONDS
    """
    logger.info("Scheduler started...")
    # Initialize to current time so it doesn't poll immediately on startup,
    # preventing database lock collision with the main startup sync thread.
    last_gmail_poll = time.time()

    while True:
        try:
            now_ts = time.time()

            # ── 1. Execute due scheduled actions ──────────────────────────────
            db = SessionLocal()
            try:
                now_utc = datetime.utcnow()
                due_actions = db.query(SuggestedAction).filter(
                    SuggestedAction.status == "scheduled",
                    SuggestedAction.scheduled_at <= now_utc
                ).all()

                for action in due_actions:
                    try:
                        logger.info(f"Executing scheduled action {action.id} ({action.action_type})")

                        if action.action_type == "create_calendar_event":
                            result = create_calendar_event(action.payload)
                            action.execution_metadata = result

                        elif action.action_type == "send_email":
                            gmail = GmailService()
                            p = action.payload
                            gmail.send_email(p["to"], p["subject"], p["body"])
                            
                        elif action.action_type == "generate_reply":
                            gmail = GmailService()
                            p = action.payload or {}
                            to_addr = p.get("to") or "hemanthvignesh27@gmail.com"
                            subject = p.get("subject") or "Reply Draft"
                            selected_reply = p.get("selected_reply_custom") or p.get("replies", [""])[0]
                            gmail.send_email(to_addr, subject, selected_reply)

                        action.status = "executed"
                        log_action(db, "action", action.id, "execute", "success", details={"type": action.action_type})

                    except Exception as e:
                        logger.error(f"Failed to execute action {action.id}: {e}")
                        action.status = "failed"
                        log_action(db, "action", action.id, "execute", "failure", details={"error": str(e)})

                    db.commit()
            finally:
                db.close()

            # ── 2. Poll Gmail for new emails ───────────────────────────────────
            if now_ts - last_gmail_poll >= GMAIL_POLL_INTERVAL_SECONDS:
                _poll_gmail()
                last_gmail_poll = now_ts

            time.sleep(60)  # Check actions every minute

        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
            time.sleep(10)


def start_scheduler_thread():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    return thread
