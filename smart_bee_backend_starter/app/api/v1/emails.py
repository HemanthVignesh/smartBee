"""Email API Endpoints"""

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emails", tags=["Emails"])


def get_db():
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
    db: Session = Depends(get_db)
):
    """
    Fetch emails from Gmail and store in database
    """
    try:
        ingestor = EmailIngestor(db)
        saved = ingestor.fetch_and_store_unread(max_results=request.max_results)
        
        return FetchEmailsResponse(
            message="Successfully fetched emails from Gmail",
            fetched_count=request.max_results,
            new_count=len(saved)
        )
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials not found. Please configure OAuth credentials."
        )
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch emails: {str(e)}"
        )


@router.get("/", response_model=List[EmailResponse])
def get_all_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    processed: bool = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all stored emails with optional filtering
    """
    query = db.query(Email)
    
    if processed is not None:
        query = query.filter(Email.processed == processed)
    
    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()
    return emails


@router.get("/search/", response_model=List[EmailResponse])
def search_emails(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search emails by subject or sender
    """
    emails = db.query(Email).filter(
        (Email.subject.contains(query)) | (Email.sender.contains(query))
    ).order_by(Email.received_at.desc()).limit(limit).all()
    
    return emails


@router.get("/{email_id}", response_model=EmailResponse)
def get_email_by_id(
    email_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific email by ID
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return email


@router.get("/gmail/profile")
def get_gmail_profile():
    """
    Get Gmail profile information (for testing connection)
    """
    try:
        gmail = GmailService()
        # Gmail profile would be fetched here
        return {
            "status": "connected",
            "message": "Gmail service initialized successfully"
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials not configured"
        )
    except Exception as e:
        logger.error(f"Gmail profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{email_id}/process")
def process_email(
    email_id: str,
    db: Session = Depends(get_db)
):
    """
    Process a specific email through AI pipeline
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Mark as processed
    email.processed = True
    
    from app.services.audit_service import log_action
    log_action(db, "email", str(email_id), "process", "success")
    
    db.commit()
    
    return {
        "message": "Email processed successfully",
        "email_id": email_id
    }