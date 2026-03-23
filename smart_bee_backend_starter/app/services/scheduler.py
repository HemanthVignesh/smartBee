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

def run_scheduler():
    """
    Simple background loop to process scheduled actions.
    """
    logger.info("Scheduler started...")
    while True:
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Find scheduled actions that are due
            due_actions = db.query(SuggestedAction).filter(
                SuggestedAction.status == "scheduled",
                SuggestedAction.scheduled_at <= now
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
                    
                    action.status = "executed"
                    log_action(db, "action", action.id, "execute", "success", details={"type": action.action_type})
                    
                except Exception as e:
                    logger.error(f"Failed to execute action {action.id}: {e}")
                    action.status = "failed"
                    log_action(db, "action", action.id, "execute", "failure", details={"error": str(e)})
                
                db.commit()
            
            db.close()
            time.sleep(60) # Check every minute
            
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
            time.sleep(10)

def start_scheduler_thread():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    return thread
