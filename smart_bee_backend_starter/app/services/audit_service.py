from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from typing import Optional, Any

def log_action(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    status: str,
    user_id: Optional[str] = None,
    details: Optional[Any] = None
):
    """
    Log an action to the audit trail.
    """
    audit = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        status=status,
        user_id=user_id,
        details=details
    )
    db.add(audit)
    db.commit()
    return audit
