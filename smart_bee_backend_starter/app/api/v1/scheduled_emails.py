from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional, List

from app.db.session import SessionLocal
from app.models.action import SuggestedAction
from app.services.ai_engine.llm_client import LLMClient

router = APIRouter(prefix="/scheduled", tags=["Scheduled Emails"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EmailUpdate(BaseModel):
    to: str
    subject: str
    body: str

@router.get("/")
def get_scheduled_emails(db: Session = Depends(get_db)):
    """Retrieve all suggested actions representing emails"""
    actions = db.query(SuggestedAction).filter(
        SuggestedAction.action_type.in_(["send_email", "generate_reply"])
    ).order_by(SuggestedAction.created_at.desc()).all()
    
    formatted = []
    for action in actions:
        payload = action.payload or {}
        
        # Extract fields based on action_type
        if action.action_type == "generate_reply":
            # Might be list of replies or a single string
            replies = payload.get("replies", [])
            body = replies[0] if isinstance(replies, list) and replies else payload.get("body", "")
            to_addr = payload.get("to") or "hemanthvignesh27@gmail.com"
            subject = payload.get("subject", "Reply Draft")
        else:
            body = payload.get("body", "")
            to_addr = payload.get("to") or "hemanthvignesh27@gmail.com"
            subject = payload.get("subject", "")
            
        # Format time and date
        scheduled_dt = action.scheduled_at
        if not scheduled_dt:
            scheduled_dt = datetime.now() + timedelta(hours=2) # fallback dummy
            
        time_str = scheduled_dt.strftime("%I:%M %p")
        date_str = scheduled_dt.strftime("%b %d, %Y")
        
        # Map DB status to frontend status
        status = action.status
        if status == "pending":
            status = "pending"
        elif status == "scheduled":
            status = "ready"
        elif status == "executed":
            status = "executed"
        elif status == "paused":
            status = "draft" # map to draft in frontend
            
        formatted.append({
            "id": action.id,
            "to": to_addr,
            "subject": subject,
            "scheduledTime": time_str,
            "date": date_str,
            "status": status,
            "preview": body[:120] + ("..." if len(body) > 120 else ""),
            "fullContent": body,
            "isAIGenerated": action.action_type == "generate_reply" or payload.get("is_ai_generated", True),
            "priority": payload.get("priority", "medium")
        })
        
    return formatted

@router.put("/{action_id}")
def update_scheduled_email(
    action_id: str,
    update_data: EmailUpdate,
    db: Session = Depends(get_db)
):
    """Update email details inside suggested action payload"""
    action = db.query(SuggestedAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Scheduled action not found")
        
    payload = action.payload or {}
    if action.action_type == "generate_reply":
        payload["replies"] = [update_data.body]
        payload["to"] = "hemanthvignesh27@gmail.com"
        payload["subject"] = update_data.subject
    else:
        payload["body"] = update_data.body
        payload["to"] = "hemanthvignesh27@gmail.com"
        payload["subject"] = update_data.subject
        
    action.payload = payload
    flag_modified(action, "payload")
    db.commit()
    return {"message": "Email details updated successfully", "id": action_id}

@router.post("/{action_id}/pause")
def pause_scheduled_email(action_id: str, db: Session = Depends(get_db)):
    """Pause email scheduling (set status to paused/draft)"""
    action = db.query(SuggestedAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Scheduled action not found")
        
    action.status = "paused"
    db.commit()
    return {"message": "Email paused successfully", "id": action_id, "status": "draft"}

@router.post("/{action_id}/resume")
def resume_scheduled_email(action_id: str, db: Session = Depends(get_db)):
    """Resume email scheduling (set status to scheduled/ready)"""
    action = db.query(SuggestedAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Scheduled action not found")
        
    action.status = "scheduled"
    if not action.scheduled_at:
        action.scheduled_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    return {"message": "Email resumed successfully", "id": action_id, "status": "ready"}

@router.post("/{action_id}/rewrite")
def rewrite_scheduled_email(
    action_id: str,
    instruction: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Use AI to rewrite email body in action payload"""
    action = db.query(SuggestedAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Scheduled action not found")
        
    payload = action.payload or {}
    if action.action_type == "generate_reply":
        replies = payload.get("replies", [])
        body = replies[0] if isinstance(replies, list) and replies else payload.get("body", "")
    else:
        body = payload.get("body", "")
        
    if not body:
         raise HTTPException(status_code=400, detail="Email body is empty, cannot rewrite")
         
    # Call AI Client
    llm = LLMClient()
    system_prompt = "You are a professional email editor. Rewrite the email body based on the instruction."
    prompt = f"Original email:\n{body}\n\nInstruction: {instruction}\n\nRewritten Email:"
    
    rewritten_text = llm.generate_completion(prompt, system_prompt=system_prompt)
    
    # Save back
    if action.action_type == "generate_reply":
        payload["replies"] = [rewritten_text]
    else:
        payload["body"] = rewritten_text
        
    action.payload = payload
    flag_modified(action, "payload")
    db.commit()
    
    return {
        "message": "Email rewritten successfully",
        "id": action_id,
        "fullContent": rewritten_text,
        "preview": rewritten_text[:120] + ("..." if len(rewritten_text) > 120 else "")
    }


@router.delete("/{action_id}")
def delete_scheduled_email(action_id: str, db: Session = Depends(get_db)):
    """Delete a suggested action representing a scheduled email/draft"""
    action = db.query(SuggestedAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Scheduled email not found")
        
    db.delete(action)
    db.commit()
    return {"message": "Scheduled email deleted successfully", "id": action_id}
