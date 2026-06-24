from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.models.decision import Decision
from app.schemas.insight import InsightResponse
from app.schemas.action import SuggestedActionResponse
from app.models.analysis import EmailAnalysis

router = APIRouter(prefix="/insights", tags=["Insights"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[InsightResponse])
def get_ai_insights(db: Session = Depends(get_db)):
    """
    Get AI insights aggregated by email analysis.
    """
    analyses = db.query(EmailAnalysis).order_by(EmailAnalysis.created_at.desc()).all()
    
    insights = []
    
    for analysis in analyses:
        email = analysis.email
        if not email:
            continue
            
        # Get decisions and actions for this email
        decision = db.query(Decision).filter_by(email_id=email.id).first()
        actions = []
        rationale = None
        if decision:
            rationale = decision.rationale
            suggested_actions = db.query(SuggestedAction).filter_by(decision_id=decision.id).all()
            for sa in suggested_actions:
                actions.append(
                    SuggestedActionResponse(
                        action_id=sa.id,
                        action_type=sa.action_type,
                        payload=sa.payload,
                        status=sa.status,
                        execution_metadata=sa.execution_metadata
                    )
                )

        # Filter: only display insights that need review/action (have pending/suggested actions)
        # or non-primary emails that have been explicitly analyzed by user request
        if len(actions) == 0 and email.category == "primary":
            continue

        insights.append(
            InsightResponse(
                email_id=email.id,
                sender=email.sender,
                subject=email.subject,
                received_at=email.received_at,
                category=email.category,
                summary=analysis.summary,
                intent=analysis.intent,
                priority=analysis.priority,
                confidence=analysis.confidence,
                entities=analysis.entities or {},
                actions=actions,
                rationale=rationale
            )
        )

    return insights