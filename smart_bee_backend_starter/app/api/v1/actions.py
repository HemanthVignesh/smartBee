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

    # -------- ACCEPT --------
    if feedback_type == "accepted":

        if action_type == "create_calendar_event":
            # 🔥 EXECUTE CALENDAR EVENT
            result = create_calendar_event(action.payload)

            action.status = "executed"
            action.execution_metadata = result
        else:
            action.status = "accepted"

    # -------- REJECT --------
    elif feedback_type == "rejected":
        action.status = "rejected"

    else:
        raise HTTPException(status_code=400, detail="Invalid feedback type")
    if feedback.feedback_type == "accepted":

        if action.action_type == "generate_reply":
            action.status = "executed"
            action.execution_metadata = {
                "selected_reply": action.payload["replies"][0]
            }

    # Store feedback
    user_feedback = UserFeedback(
        action_id=action_id,
        feedback_type=feedback_type
    )

    db.add(user_feedback)
    db.commit()
    db.refresh(action)

    return {
        "message": "Action processed",
        "status": action.status,
        "execution_metadata": action.execution_metadata
    }
    
