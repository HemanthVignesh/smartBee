from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.email import Email
from app.schemas.email import EmailResponse
from app.services.ingestion.email_ingestor import EmailIngestor

router = APIRouter(prefix="/emails", tags=["Emails"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/process")
def process_emails(db: Session = Depends(get_db)):
    ingestor = EmailIngestor(db)
    saved = ingestor.fetch_and_store_unread()
    return {"saved_count": len(saved)}

@router.get("/", response_model=list[EmailResponse])
def get_emails(db: Session = Depends(get_db)):
    return db.query(Email).order_by(Email.received_at.desc()).all()
