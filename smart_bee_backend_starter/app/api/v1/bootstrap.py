from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import uuid

from app.db.session import SessionLocal
from app.models.email import Email
from app.models.analysis import EmailAnalysis
from app.models.decision import Decision
from app.models.action import SuggestedAction
from app.models.chat_history import ChatHistory
from app.models.audit import AuditLog

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/bootstrap", tags=["Bootstrap"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/sync")
def sync_gmail_now(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an immediate Gmail fetch and AI processing pipeline.
    Uses real email data from the authenticated Gmail account.
    """
    try:
        from app.services.ingestion.email_ingestor import EmailIngestor
        ingestor = EmailIngestor(db, user_id=current_user.id)
        
        if ingestor.gmail.mock_mode:
            return {
                "status": "not_configured",
                "message": "Gmail is not configured. Please add OAuth2 credentials (credentials.json) to enable real email sync.",
                "new_emails": 0
            }
        
        saved = ingestor.fetch_and_store_unread(max_results=25)
        return {
            "status": "success",
            "message": f"Successfully synced {len(saved)} new email(s) from Gmail.",
            "new_emails": len(saved)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail sync failed: {str(e)}")


@router.delete("/clear")
def clear_all_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clears current user's data from the database.
    """
    try:
        user_emails = db.query(Email).filter(Email.user_id == current_user.id).all()
        user_email_ids = [e.id for e in user_emails]
        user_decisions = db.query(Decision).filter(Decision.email_id.in_(user_email_ids)).all()
        user_decision_ids = [d.id for d in user_decisions]

        db.query(SuggestedAction).filter(SuggestedAction.decision_id.in_(user_decision_ids)).delete()
        db.query(Decision).filter(Decision.id.in_(user_decision_ids)).delete()
        db.query(EmailAnalysis).filter(EmailAnalysis.email_id.in_(user_email_ids)).delete()
        db.query(Email).filter(Email.user_id == current_user.id).delete()
        db.query(ChatHistory).filter(ChatHistory.session_id.like(f"{current_user.id}:%")).delete()
        db.query(AuditLog).filter(AuditLog.user_id == current_user.id).delete()
        
        db.commit()
        return {"message": "✅ Your data cleared. The app is ready for a fresh Gmail sync."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.post("/")
def bootstrap_mock_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clears current user's tables and seeds the database with premium, realistic mock data
    for demoing the Smart Bee features.
    """

    try:
        # Clear tables for this user first
        user_emails = db.query(Email).filter(Email.user_id == current_user.id).all()
        user_email_ids = [e.id for e in user_emails]
        user_decisions = db.query(Decision).filter(Decision.email_id.in_(user_email_ids)).all()
        user_decision_ids = [d.id for d in user_decisions]

        db.query(SuggestedAction).filter(SuggestedAction.decision_id.in_(user_decision_ids)).delete()
        db.query(Decision).filter(Decision.id.in_(user_decision_ids)).delete()
        db.query(EmailAnalysis).filter(EmailAnalysis.email_id.in_(user_email_ids)).delete()
        db.query(Email).filter(Email.user_id == current_user.id).delete()
        db.query(ChatHistory).filter(ChatHistory.session_id.like(f"{current_user.id}:%")).delete()
        db.query(AuditLog).filter(AuditLog.user_id == current_user.id).delete()
        db.commit()
        
        # 1. Create mock emails
        email_1 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-101",
            sender="sarah.connor@cyberdyne.com",
            subject="Smart Bee Project Roadmap Zoom",
            body="Hi Hemanth, can we schedule a Zoom call tomorrow at 10 AM to discuss the Smart Bee project roadmap? Let me know what times work for you. Thanks, Sarah.",
            received_at=datetime.utcnow() - timedelta(hours=2),
            processed=False,
            category="primary",
            user_id=current_user.id
        )
        
        email_2 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-102",
            sender="teamlead@smartbee.ai",
            subject="Urgent: Slide Deck Deadline",
            body="Hey Hemanth, please remember that the client presentation slides are due on 2026-06-15. We need to upload them before 5 PM to the shared drive. Let's make sure it's fully reviewed.",
            received_at=datetime.utcnow() - timedelta(hours=5),
            processed=False,
            category="updates",
            user_id=current_user.id
        )
        
        email_3 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-103",
            sender="billing@studioco.design",
            subject="Invoice #10923 for Design Services",
            body="Hello, attached is invoice #10923 for the design services completed last month. Please process the payment by next Monday. Thank you!",
            received_at=datetime.utcnow() - timedelta(days=1),
            processed=False,
            category="updates",
            user_id=current_user.id
        )
        
        email_4 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-104",
            sender="no-reply@aws.amazon.com",
            subject="AWS Server Migration Complete",
            body="Weekly AWS update: Our server performance has improved by 20% after the migration. All endpoints are healthy. No action is required.",
            received_at=datetime.utcnow() - timedelta(days=2),
            processed=True,
            category="updates",
            user_id=current_user.id
        )

        email_5 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-105",
            sender="alert@mailer.ajio.in",
            subject="Wait...You’re leaving this behind? 😱",
            body="Hey Hemanth, items in your cart are selling fast! Complete your purchase now and get an extra 15% off using code BAG15. Click here to checkout.",
            received_at=datetime.utcnow() - timedelta(hours=1),
            processed=False,
            category="promotions",
            user_id=current_user.id
        )

        email_6 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-106",
            sender="close_friend_updates@facebookmail.com",
            subject="Post by Anand Kumar Vuttaradi",
            body="Anand Kumar Vuttaradi posted a new update on your timeline: 'Hey Hemanth, are we still on for the hackathon planning this weekend?' Click here to reply.",
            received_at=datetime.utcnow() - timedelta(minutes=45),
            processed=False,
            category="social",
            user_id=current_user.id
        )

        email_7 = Email(
            id=str(uuid.uuid4()),
            message_id="msg-107",
            sender="notifications@github.com",
            subject="[GitHub] Community Discussion: Next.js 15 App Router Transitions",
            body="A new discussion thread has been opened in the Next.js repository: 'Layout transitions in Next.js 15: Flash of unstyled content under heavy load'. Several maintainers have commented on workarounds.",
            received_at=datetime.utcnow() - timedelta(hours=3),
            processed=False,
            category="forums",
            user_id=current_user.id
        )
        
        db.add_all([email_1, email_2, email_3, email_4, email_5, email_6, email_7])
        db.flush()
        
        # 2. Add Analyses
        analysis_1 = EmailAnalysis(
            email_id=email_1.id,
            intent="meeting_request",
            priority="high",
            confidence=0.92,
            summary="Sarah Connor requested a Zoom meeting tomorrow at 10 AM to discuss the roadmap.",
            entities={"dates": ["tomorrow"], "times": ["10 AM"], "people": ["Sarah"]},
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        analysis_2 = EmailAnalysis(
            email_id=email_2.id,
            intent="task_assignment",
            priority="high",
            confidence=0.88,
            summary="Slide deck upload deadline is due 2026-06-15 at 5 PM.",
            entities={"dates": ["2026-06-15"], "times": ["5 PM"], "people": []},
            created_at=datetime.utcnow() - timedelta(hours=5)
        )
        
        analysis_3 = EmailAnalysis(
            email_id=email_3.id,
            intent="general",
            priority="medium",
            confidence=0.85,
            summary="Invoice invoice for design services due by next Monday.",
            entities={"dates": ["next Monday"], "times": [], "people": []},
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        
        analysis_4 = EmailAnalysis(
            email_id=email_4.id,
            intent="general",
            priority="low",
            confidence=0.95,
            summary="AWS migration completed successfully. Server performance improved by 20%.",
            entities={},
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        
        db.add_all([analysis_1, analysis_2, analysis_3, analysis_4])
        
        # 3. Add Decisions
        decision_1 = Decision(
            email_id=email_1.id,
            decision_type="meeting_request",
            rationale="Meeting request keywords and specific date/time slots detected.",
            auto_executable=False,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        decision_2 = Decision(
            email_id=email_2.id,
            decision_type="task_assignment",
            rationale="Task deadline explicitly stated for a future date.",
            auto_executable=False,
            created_at=datetime.utcnow() - timedelta(hours=5)
        )
        
        decision_3 = Decision(
            email_id=email_3.id,
            decision_type="general",
            rationale="Invoice details detected. Categorized as payment task.",
            auto_executable=False,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        
        db.add_all([decision_1, decision_2, decision_3])
        db.flush()
        
        # 4. Add Suggested Actions
        action_1 = SuggestedAction(
            id=f"act-event-{uuid.uuid4()}",
            decision_id=decision_1.id,
            action_type="create_calendar_event",
            payload={
                "title": "Roadmap discussion with Sarah Connor",
                "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "10:00"
            },
            status="pending",
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
        action_2 = SuggestedAction(
            id=f"act-reply-{uuid.uuid4()}",
            decision_id=decision_2.id,
            action_type="generate_reply",
            payload={
                "replies": [
                    "Hi, thanks for the reminder. I am finalizing the slides now and will upload them way before 5 PM on Monday. Best, Hemanth."
                ],
                "to": "teamlead@smartbee.ai",
                "subject": "Re: Slide Deck Deadline",
                "priority": "high",
                "is_ai_generated": True
            },
            status="pending",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )

        # Scheduled Email 1 (Ready / Auto-send status in DB)
        action_3 = SuggestedAction(
            id=f"scheduled-email-1-{uuid.uuid4()}",
            decision_id=decision_1.id,
            action_type="send_email",
            payload={
                "to": "john.doe@example.com",
                "subject": "Quarterly Report Review",
                "body": "Hi John,\n\nI wanted to share the quarterly report for your review. The numbers look great this quarter - we've exceeded our targets by 15%.\n\nKey highlights:\n• Revenue up 18%\n• Customer satisfaction at 94%\n• New clients: 23\n\nPlease let me know if you have any questions or would like to discuss further.\n\nBest regards,\nHemanth",
                "priority": "high",
                "is_ai_generated": True
            },
            status="scheduled",
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            created_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )

        # Scheduled Email 2 (Paused status in DB)
        action_4 = SuggestedAction(
            id=f"scheduled-email-2-{uuid.uuid4()}",
            decision_id=decision_2.id,
            action_type="send_email",
            payload={
                "to": "sarah.wilson@example.com",
                "subject": "Follow-up on Proposal",
                "body": "Hi Sarah,\n\nFollowing up on the proposal we discussed last week.\n\nI've attached the updated version with the changes we talked about.\n\nWould love to get your thoughts when you have a chance.\n\nThanks,\nHemanth",
                "priority": "low",
                "is_ai_generated": False
            },
            status="paused",
            scheduled_at=datetime.utcnow() + timedelta(days=2),
            created_at=datetime.now(timezone.utc) - timedelta(hours=3)
        )

        # Scheduled Email 3 (Pending approval status in DB)
        action_5 = SuggestedAction(
            id=f"scheduled-email-3-{uuid.uuid4()}",
            decision_id=decision_3.id,
            action_type="send_email",
            payload={
                "to": "client@business.com",
                "subject": "Project Milestone Delivery",
                "body": "Dear Client,\n\nI'm pleased to inform you that we've reached an important milestone in your project.\n\nWe've completed Phase 2 ahead of schedule and are ready to move to final testing.\n\nWould you be available for a demo next week?\n\nBest regards,\nHemanth",
                "priority": "urgent",
                "is_ai_generated": True
            },
            status="pending",
            scheduled_at=datetime.utcnow() + timedelta(hours=4),
            created_at=datetime.now(timezone.utc) - timedelta(hours=6)
        )

        # Executed Meeting 1 (Product Strategy Review)
        action_meeting_1 = SuggestedAction(
            id=f"scheduled-meeting-1-{uuid.uuid4()}",
            decision_id=decision_1.id,
            action_type="create_calendar_event",
            payload={
                "title": "Product Strategy Review",
                "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "10:00 AM",
                "duration": "1h",
                "attendees": ["Alex Chen", "Maria Garcia", "Tom Brown"],
                "priority": "high"
            },
            status="executed",
            execution_metadata={
                "event_id": "mock-event-1",
                "event_link": "https://calendar.google.com/calendar/render"
            },
            created_at=datetime.now(timezone.utc) - timedelta(hours=3)
        )

        # Executed Meeting 2 (Client Presentation)
        action_meeting_2 = SuggestedAction(
            id=f"scheduled-meeting-2-{uuid.uuid4()}",
            decision_id=decision_1.id,
            action_type="create_calendar_event",
            payload={
                "title": "Client Presentation",
                "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "03:00 PM",
                "duration": "45m",
                "attendees": ["Jennifer Lee", "Robert Smith"],
                "priority": "high"
            },
            status="executed",
            execution_metadata={
                "event_id": "mock-event-2",
                "event_link": "https://calendar.google.com/calendar/render"
            },
            created_at=datetime.now(timezone.utc) - timedelta(hours=4)
        )
        
        db.add_all([action_1, action_2, action_3, action_4, action_5, action_meeting_1, action_meeting_2])
        
        # 5. Add Chat History namespaces to user
        chat_1 = ChatHistory(
            session_id=f"{current_user.id}:default_session",
            role="assistant",
            content="Hi Hemanth! I have seeded the demo environment. You have 3 new emails and 2 pending actions to review on your dashboard.",
            created_at=datetime.utcnow() - timedelta(minutes=10)
        )
        
        db.add(chat_1)
        
        # 6. Add Audit Logs
        log_1 = AuditLog(
            entity_type="email",
            entity_id=email_1.id,
            action="ingest",
            status="success",
            user_id=current_user.id,
            details={"subject": email_1.subject},
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        log_2 = AuditLog(
            entity_type="email",
            entity_id=email_2.id,
            action="ingest",
            status="success",
            user_id=current_user.id,
            details={"subject": email_2.subject},
            created_at=datetime.utcnow() - timedelta(hours=5)
        )
        
        log_3 = AuditLog(
            entity_type="action",
            entity_id=action_1.id,
            action="suggest",
            status="success",
            user_id=current_user.id,
            details={"action_type": "create_calendar_event"},
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db.add_all([log_1, log_2, log_3])
        
        db.commit()
        return {"message": "Database successfully bootstrapped with premium mock data"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed database: {str(e)}")
