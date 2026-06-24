from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.email import Email
from app.models.action import SuggestedAction
from app.models.audit import AuditLog
from app.schemas.analytics import AnalyticsStats

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats", response_model=AnalyticsStats)
def get_analytics_stats(db: Session = Depends(get_db)):
    """
    Get aggregated analytics for the dashboard.
    """
    total_emails = db.query(Email).count()
    processed_emails = db.query(Email).filter_by(processed=True).count()
    actions_count = db.query(SuggestedAction).count()
    
    # Calculate time saved (e.g., 5 mins per email, 15 mins per meeting scheduled)
    # This is a heuristic for the "production" feel
    time_saved_minutes = (processed_emails * 5) + (actions_count * 15)
    time_saved_hours = round(time_saved_minutes / 60, 1)
    
    # Calculate emails per week (last 7 days)
    emails_per_week = []
    today = datetime.utcnow().date()
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        day_name = target_date.strftime("%a")
        
        received_count = db.query(Email).filter(
            func.date(Email.received_at) == target_date
        ).count()
        
        # Count actions created on target_date
        sent_count = db.query(SuggestedAction).filter(
            func.date(SuggestedAction.created_at) == target_date
        ).count()
        
        emails_per_week.append({
            "day": day_name,
            "sent": sent_count,
            "received": received_count
        })

    # Calculate time saved trend (last 4 weeks)
    time_saved_trend = []
    for w in range(3, -1, -1):
        start_date = today - timedelta(weeks=w+1)
        end_date = today - timedelta(weeks=w)
        
        processed_wk = db.query(Email).filter(
            Email.processed == True,
            Email.received_at >= datetime.combine(start_date, datetime.min.time()),
            Email.received_at < datetime.combine(end_date, datetime.max.time())
        ).count()
        
        actions_wk = db.query(SuggestedAction).filter(
            SuggestedAction.created_at >= datetime.combine(start_date, datetime.min.time()),
            SuggestedAction.created_at < datetime.combine(end_date, datetime.max.time())
        ).count()
        
        wk_saved_hours = round(((processed_wk * 5) + (actions_wk * 15)) / 60, 1)
        time_saved_trend.append({
            "week": f"Week {4-w}",
            "hours": wk_saved_hours
        })

    # Get recent audit logs
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    activity = []
    for log in recent_logs:
        activity.append({
            "action": log.action,
            "entity": log.entity_type,
            "status": log.status,
            "time": log.created_at.isoformat()
        })
        
    return AnalyticsStats(
        total_emails=total_emails,
        processed_emails=processed_emails,
        actions_count=actions_count,
        time_saved_hours=time_saved_hours,
        recent_activity=activity,
        emails_per_week=emails_per_week,
        time_saved_trend=time_saved_trend
    )
