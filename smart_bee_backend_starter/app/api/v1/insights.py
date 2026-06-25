from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.models.decision import Decision
from app.schemas.insight import InsightResponse
from app.schemas.action import SuggestedActionResponse
from app.models.analysis import EmailAnalysis
from app.models.email import Email
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/insights", tags=["Insights"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[InsightResponse])
def get_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI insights for the authenticated user's emails only."""
    # Scoped join: only analyses whose email belongs to current_user
    analyses = (
        db.query(EmailAnalysis)
        .join(Email, EmailAnalysis.email_id == Email.id)
        .filter(Email.user_id == current_user.id)
        .order_by(EmailAnalysis.created_at.desc())
        .all()
    )

    insights = []
    for analysis in analyses:
        email = analysis.email
        if not email:
            continue

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
                        execution_metadata=sa.execution_metadata,
                    )
                )

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
                rationale=rationale,
            )
        )

    return insights