"""Email API Endpoints — UPDATED: all routes require authentication.
Each user only sees emails where email.user_id matches their JWT sub.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import logging

from app.db.session import SessionLocal
from app.services.ingestion.gmail_service import GmailService
from app.services.ingestion.email_ingestor import EmailIngestor
from app.models.email import Email
from app.schemas.email import EmailResponse
from app.auth.dependencies import get_current_user   # ← NEW
from app.models.user import User                      # ← NEW

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emails", tags=["Emails"])


def get_db():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FetchEmailsRequest(BaseModel):
    max_results: int = 10


class FetchEmailsResponse(BaseModel):
    message: str
    fetched_count: int
    new_count: int


@router.post("/fetch", response_model=FetchEmailsResponse)
def fetch_emails_from_gmail(
    request: FetchEmailsRequest = FetchEmailsRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Fetch emails from Gmail and store them scoped to the authenticated user."""
    try:
        ingestor = EmailIngestor(db, user_id=current_user.id)   # pass user_id
        saved = ingestor.fetch_and_store_unread(max_results=request.max_results)

        return FetchEmailsResponse(
            message="Successfully fetched emails from Gmail",
            fetched_count=request.max_results,
            new_count=len(saved),
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials not found. Please configure OAuth credentials.",
        )
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.get("/", response_model=List[EmailResponse])
def get_all_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    processed: bool = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Get emails belonging to the authenticated user only."""
    query = db.query(Email).filter(Email.user_id == current_user.id)   # ← SCOPED

    if processed is not None:
        query = query.filter(Email.processed == processed)

    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()
    return emails


@router.get("/search/", response_model=List[EmailResponse])
def search_emails(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Search emails scoped to the authenticated user."""
    emails = (
        db.query(Email)
        .filter(
            Email.user_id == current_user.id,          # ← SCOPED
            (Email.subject.contains(query)) | (Email.sender.contains(query)),
        )
        .order_by(Email.received_at.desc())
        .limit(limit)
        .all()
    )
    return emails


@router.get("/gmail/profile")
def get_gmail_profile(current_user: User = Depends(get_current_user)):   # ← NEW
    """Return Gmail connection status for the authenticated user."""
    try:
        gmail = GmailService()
        return {
            "status": "connected",
            "email": current_user.email,
            "message": "Gmail service initialised successfully",
        }
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Gmail credentials not configured")
    except Exception as e:
        logger.error(f"Gmail profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{email_id}", response_model=EmailResponse)
def get_email_by_id(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Get a specific email — only if it belongs to the current user."""
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.user_id == current_user.id)   # ← SCOPED
        .first()
    )

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email


@router.post("/{email_id}/process")
def process_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Process a specific email (must belong to the current user)."""
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.user_id == current_user.id)
        .first()
    )

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.processed = True

    from app.services.audit_service import log_action
    log_action(db, "email", str(email_id), "process", "success", user_id=current_user.id)

    db.commit()

    return {"message": "Email processed successfully", "email_id": email_id}


@router.post("/{email_id}/analyze")
def analyze_email_on_demand(
    email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← NEW
):
    """Manually trigger AI analysis for a specific email."""
    # Verify ownership before processing
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.user_id == current_user.id)
        .first()
    )
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    from app.services.email_processor import EmailProcessor
    processor = EmailProcessor(db)
    result = processor.process_email(email_id, force=True)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
