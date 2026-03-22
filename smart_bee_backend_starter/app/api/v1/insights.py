from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session



from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.schemas.insight import InsightResponse
from app.schemas.action import SuggestedActionResponse

router = APIRouter(prefix="/insights", tags=["AI Insights"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[InsightResponse])
def get_ai_insights(db: Session = Depends(get_db)):

    actions = db.query(SuggestedAction).all()

    insights_map = {}

    for action in actions:
        decision = action.decision
        email = decision.email

        if decision.id not in insights_map:
            insights_map[decision.id] = {
                "email_id": email.id,
                "summary": decision.rationale,
                "intent": decision.decision_type,
                "priority": "high",
                "confidence": 0.85,
                "entities": {},
                "actions": []
            }

        insights_map[decision.id]["actions"].append(
            SuggestedActionResponse(
                action_id=action.id,
                action_type=action.action_type,
                payload=action.payload,
                status=action.status,
                execution_metadata=action.execution_metadata
            )
        )

    return [InsightResponse(**data) for data in insights_map.values()]