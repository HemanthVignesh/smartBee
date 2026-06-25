from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.email import Email
from app.models.action import SuggestedAction
from app.models.audit import AuditLog
from app.schemas.analytics import AnalyticsStats
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats", response_model=AnalyticsStats)
def get_analytics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated analytics scoped to the authenticated user."""
    uid = current_user.id

    total_emails = db.query(Email).filter(Email.user_id == uid).count()
    processed_emails = db.query(Email).filter(Email.user_id == uid, Email.processed == True).count()

    # Actions linked to this user's emails only (via Decision → Email)
    from app.models.decision import Decision
    user_decision_ids = [
        d.id for d in db.query(Decision.id)
        .join(Email, Decision.email_id == Email.id)
        .filter(Email.user_id == uid)
        .all()
    ]
    actions_count = (
        db.query(SuggestedAction)
        .filter(SuggestedAction.decision_id.in_(user_decision_ids))
        .count()
    )

    time_saved_minutes = (processed_emails * 5) + (actions_count * 15)
    time_saved_hours = round(time_saved_minutes / 60, 1)

    today = datetime.utcnow().date()
    emails_per_week = []
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        day_name = target_date.strftime("%a")
        received_count = db.query(Email).filter(
            Email.user_id == uid,
            func.date(Email.received_at) == target_date,
        ).count()
        sent_count = db.query(SuggestedAction).filter(
            SuggestedAction.decision_id.in_(user_decision_ids),
            func.date(SuggestedAction.created_at) == target_date,
        ).count()
        emails_per_week.append({"day": day_name, "sent": sent_count, "received": received_count})

    time_saved_trend = []
    for w in range(3, -1, -1):
        start_date = today - timedelta(weeks=w + 1)
        end_date = today - timedelta(weeks=w)
        processed_wk = db.query(Email).filter(
            Email.user_id == uid,
            Email.processed == True,
            Email.received_at >= datetime.combine(start_date, datetime.min.time()),
            Email.received_at < datetime.combine(end_date, datetime.max.time()),
        ).count()
        actions_wk = db.query(SuggestedAction).filter(
            SuggestedAction.decision_id.in_(user_decision_ids),
            SuggestedAction.created_at >= datetime.combine(start_date, datetime.min.time()),
            SuggestedAction.created_at < datetime.combine(end_date, datetime.max.time()),
        ).count()
        time_saved_trend.append({
            "week": f"Week {4 - w}",
            "hours": round(((processed_wk * 5) + (actions_wk * 15)) / 60, 1),
        })

    recent_logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == uid)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    activity = [
        {"action": log.action, "entity": log.entity_type, "status": log.status, "time": log.created_at.isoformat()}
        for log in recent_logs
    ]

    return AnalyticsStats(
        total_emails=total_emails,
        processed_emails=processed_emails,
        actions_count=actions_count,
        time_saved_hours=time_saved_hours,
        recent_activity=activity,
        emails_per_week=emails_per_week,
        time_saved_trend=time_saved_trend,
    )
