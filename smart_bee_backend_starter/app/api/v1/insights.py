from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.models.decision import Decision
from app.schemas.insight import InsightResponse
from app.schemas.action import SuggestedActionResponse



from app.models.analysis import EmailAnalysis

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
        if decision:
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

        insights.append(
            InsightResponse(
                email_id=email.id,
                summary=analysis.summary,
                intent=analysis.intent,
                priority=analysis.priority,
                confidence=analysis.confidence,
                entities=analysis.entities or {},
                actions=actions
            )
        )

    return insights