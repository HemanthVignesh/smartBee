from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db.session import SessionLocal
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.ai_engine.llm_client import LLMClient
from app.models.chat_history import ChatHistory
from app.models.email import Email
from app.auth.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with the Smart Bee AI assistant and execute agent tools.
    """
    try:
        session_id = f"{current_user.id}:{request.session_id or 'default_session'}"
        
        # 1. Store User message
        user_msg = ChatHistory(session_id=session_id, role="user", content=request.message)
        db.add(user_msg)
        db.commit()
        
        # 2. Call ChatbotAgent to interpret intent and run tools
        from app.services.ai_engine.chatbot_agent import ChatbotAgent
        agent = ChatbotAgent()
        response_text = agent.handle_chat(request.message, db, session_id=session_id)
        
        # 3. Store Assistant message
        assistant_msg = ChatHistory(session_id=session_id, role="assistant", content=response_text)
        db.add(assistant_msg)
        
        # 4. Log to audit
        from app.services.audit_service import log_action
        log_action(db, "chatbot", session_id, "chat", "success", user_id=current_user.id)
        
        db.commit()
        
        return ChatResponse(
            response=response_text,
            context_used=True
        )
        
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_chat_history(
    session_id: str = "default_session",
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve chat history for a session.
    """
    try:
        namespaced_session = f"{current_user.id}:{session_id}"
        history = db.query(ChatHistory).filter_by(
            session_id=namespaced_session
        ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
        history.reverse()
        
        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in history
        ]
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
def clear_chat_history(
    session_id: str = "default_session",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all chat history for a session.
    """
    try:
        namespaced_session = f"{current_user.id}:{session_id}"
        deleted = db.query(ChatHistory).filter_by(session_id=namespaced_session).delete()
        db.commit()
        return {"message": f"Cleared {deleted} messages"}
    except Exception as e:
        logger.error(f"Chat clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
