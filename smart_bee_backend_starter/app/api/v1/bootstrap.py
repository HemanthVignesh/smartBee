from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.email import Email
from app.models.decision import Decision
from app.models.action import SuggestedAction

router = APIRouter(prefix="/bootstrap", tags=["Bootstrap"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def bootstrap_data(db: Session = Depends(get_db)):
    # prevent duplicate bootstrap
    existing = db.query(SuggestedAction).filter_by(id="action_1").first()
    if existing:
        return {"message": "Already bootstrapped"}

    email = Email(
        message_id="msg_123",
        sender="boss@company.com",
        subject="Project discussion",
        body="Let’s meet tomorrow to discuss Smart BEE",
        source="mock"
    )
    db.add(email)
    db.commit()
    db.refresh(email)

    decision = Decision(
        email_id=email.id,
        decision_type="meeting_request",
        rationale="Detected meeting intent"
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    action = SuggestedAction(
        id="action_1",
        decision_id=decision.id,
        action_type="create_calendar_event",
        payload={"date": "2026-01-28", "time": "10:00"}
    )
    db.add(action)
    db.commit()

    return {"message": "Bootstrap complete"}
