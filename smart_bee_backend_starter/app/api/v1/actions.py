# Action confirmation endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.executors.calendar_executor import create_calendar_event
from app.db.session import SessionLocal
from app.schemas.feedback import FeedbackRequest
from app.models.action import SuggestedAction
from app.models.feedback import UserFeedback

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.email import Email
from app.models.decision import Decision

router = APIRouter(prefix="/actions", tags=["Actions"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _assert_action_owned_by(action: SuggestedAction, user_id: str, db: Session):
    """Raise 404 (not 403 — don't leak existence) if action doesn't belong to user."""
    decision = db.query(Decision).filter_by(id=action.decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Action not found")
    email = db.query(Email).filter_by(id=decision.email_id, user_id=user_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Action not found")


@router.get("/meetings")
def get_scheduled_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all executed suggested actions that created calendar events"""
    from app.models.decision import Decision
    user_decision_ids = [
        d.id for d in db.query(Decision.id)
        .join(Email, Decision.email_id == Email.id)
        .filter(Email.user_id == current_user.id)
        .all()
    ]
    actions = db.query(SuggestedAction).filter(
        SuggestedAction.action_type == "create_calendar_event",
        SuggestedAction.status == "executed",
        SuggestedAction.decision_id.in_(user_decision_ids)
    ).order_by(SuggestedAction.created_at.desc()).all()
    
    formatted = []
    for action in actions:
        payload = action.payload or {}
        
        # Extract details
        title = payload.get("title", "Meeting Request")
        date_val = payload.get("date", "")
        time_val = payload.get("time", "")
        duration = payload.get("duration", "30m")
        priority = payload.get("priority", "medium")
        
        formatted_date = date_val
        try:
            parsed_dt = datetime.strptime(date_val, "%Y-%m-%d")
            formatted_date = parsed_dt.strftime("%b %d, %Y")
        except:
            pass

        formatted.append({
            "id": action.id,
            "title": title,
            "attendees": payload.get("attendees", ["Sarah Connor"]),
            "scheduledTime": time_val,
            "date": formatted_date,
            "duration": duration,
            "priority": priority,
            "meetingLink": action.execution_metadata.get("event_link") if action.execution_metadata else None
        })
    return formatted


@router.post("/{action_id}/feedback")
def submit_feedback(
    action_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    action = db.query(SuggestedAction).filter_by(id=action_id).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    _assert_action_owned_by(action, current_user.id, db)

    feedback_type = feedback.feedback_type.lower().strip()
    action_type = action.action_type.lower().strip()

    # Prevent double execution
    if action.status == "executed" and feedback_type == "accepted":
        return {
            "message": "Action already executed",
            "status": action.status,
            "execution_metadata": action.execution_metadata
        }

    # -------- ACCEPT --------
    if feedback_type == "accepted":
        if action_type == "create_calendar_event":
            try:
                # Merge custom user modifications if present
                payload_to_use = action.payload.copy() if action.payload else {}
                if feedback.custom_payload:
                    payload_to_use.update(feedback.custom_payload)
                
                # 🔥 EXECUTE CALENDAR EVENT
                result = create_calendar_event(payload_to_use)
                action.status = "executed"
                action.execution_metadata = result
            except Exception as e:
                action.status = "failed"
                action.execution_metadata = {"error": str(e)}
                raise HTTPException(status_code=500, detail=f"Calendar execution failed: {str(e)}")
        
        elif action_type == "generate_reply":
            selected_reply = action.payload.get("replies", ["No reply generated"])[0]
            if feedback.custom_payload and "reply_text" in feedback.custom_payload:
                selected_reply = feedback.custom_payload["reply_text"]
                # Save the custom reply version in action payload
                action_payload_copy = action.payload.copy() if action.payload else {}
                action_payload_copy["selected_reply_custom"] = selected_reply
                action.payload = action_payload_copy
            
            from app.services.ingestion.gmail_service import GmailService
            gmail = GmailService(token_json=current_user.gmail_token_json)
            to_addr = action.payload.get("to") or "hemanthvignesh27@gmail.com"
            subject = action.payload.get("subject") or "Reply Draft"
            
            success = gmail.send_email(to_addr, subject, selected_reply)
            
            if success:
                action.status = "executed"
                action.execution_metadata = {
                    "selected_reply": selected_reply,
                    "sent_at": datetime.utcnow().isoformat()
                }
            else:
                action.status = "failed"
                action.execution_metadata = {"error": "Gmail send failed"}
                raise HTTPException(status_code=500, detail="Gmail API failed to send reply email")
        
        else:
            action.status = "accepted"

    # -------- REJECT --------
    elif feedback_type == "rejected":
        action.status = "rejected"

    else:
        raise HTTPException(status_code=400, detail="Invalid feedback type")

    # Store feedback record
    user_feedback = UserFeedback(
        action_id=action_id,
        feedback_type=feedback_type
    )

    db.add(user_feedback)
    
    # Log to audit trail
    from app.services.audit_service import log_action
    log_action(db, "action", action_id, feedback_type, "success", user_id=current_user.id, details={"type": action_type})
    
    db.commit()
    db.refresh(action)

    return {
        "message": f"Action {feedback_type}",
        "status": action.status,
        "execution_metadata": action.execution_metadata
    }
