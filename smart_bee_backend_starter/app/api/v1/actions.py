# Action confirmation endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.executors.calendar_executor import create_calendar_event
from app.db.session import SessionLocal
from app.schemas.feedback import FeedbackRequest
from app.models.action import SuggestedAction
from app.models.feedback import UserFeedback

router = APIRouter(prefix="/actions", tags=["Actions"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{action_id}/feedback")
def submit_feedback(
    action_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    action = db.query(SuggestedAction).filter_by(id=action_id).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

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
                # 🔥 EXECUTE CALENDAR EVENT
                result = create_calendar_event(action.payload)
                action.status = "executed"
                action.execution_metadata = result
            except Exception as e:
                action.status = "failed"
                action.execution_metadata = {"error": str(e)}
                raise HTTPException(status_code=500, detail=f"Calendar execution failed: {str(e)}")
        
        elif action_type == "generate_reply":
            # Store the first reply as the selected one (or use index if provided in payload)
            selected_reply = action.payload.get("replies", ["No reply generated"])[0]
            action.status = "executed"
            action.execution_metadata = {
                "selected_reply": selected_reply
            }
        
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
    log_action(db, "action", action_id, feedback_type, "success", details={"type": action_type})
    
    db.commit()
    db.refresh(action)

    return {
        "message": f"Action {feedback_type}",
        "status": action.status,
        "execution_metadata": action.execution_metadata
    }

    return {
        "message": "Action processed",
        "status": action.status,
        "execution_metadata": action.execution_metadata
    }
    
