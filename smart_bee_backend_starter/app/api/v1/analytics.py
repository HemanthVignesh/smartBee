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
        recent_activity=activity
    )
