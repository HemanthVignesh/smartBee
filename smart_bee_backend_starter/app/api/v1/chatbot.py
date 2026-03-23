from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db.session import SessionLocal
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.ai_engine.llm_client import LLMClient
from app.models.chatbot_history import ChatHistory # wait I named it chat_history.py
from app.models.chat_history import ChatHistory

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
    db: Session = Depends(get_db)
):
    """
    Chat with the Smart Bee AI assistant with session persistence.
    """
    try:
        session_id = "default_session" # Could be passed in request later
        llm = LLMClient()
        
        # 1. Fetch conversation history
        history_entries = db.query(ChatHistory).filter_by(session_id=session_id).order_by(ChatHistory.created_at.asc()).limit(10).all()
        
        chat_context = []
        for entry in history_entries:
            chat_context.append({"role": entry.role, "content": entry.content})
            
        # 2. Add rich context (Latest Emails + Analysis + Decisions + Actions)
        latest_emails = db.query(Email).order_by(Email.received_at.desc()).limit(3).all()
        rich_context = ""
        
        if latest_emails:
            rich_context = "\n--- SYSTEM MEMORY: RECENT CONTEXT ---\n"
            for email in latest_emails:
                rich_context += f"Email from {email.sender}: {email.subject}\n"
                
                # Fetch analysis for this email
                if email.analysis:
                    rich_context += f"  - Intent: {email.analysis.intent}\n"
                    rich_context += f"  - Summary: {email.analysis.summary}\n"
                
                # Fetch decisions and actions
                if email.decisions:
                    for dec in email.decisions:
                        rich_context += f"  - Decision: {dec.decision_type} ({dec.rationale})\n"
                        if dec.actions:
                            for act in dec.actions:
                                rich_context += f"    - Action: {act.action_type} (Status: {act.status})\n"
                rich_context += "\n"

        system_prompt = (
            "You are Smart Bee, the user's premium AI email assistant. "
            "You have access to the user's emails and the automated analysis performed by the system. "
            "Use the 'SYSTEM MEMORY' provided below to answer user queries accurately. "
            "If asked about recent tasks or meetings, refer to the 'Action' and 'Decision' status in the memory. "
            f"{rich_context}"
            "\nBe professional, concise, and prioritize facts from the system memory."
        )
        
        # 3. Store User message
        user_msg = ChatHistory(session_id=session_id, role="user", content=request.message)
        db.add(user_msg)
        
        # 4. Generate response
        # Note: LLMClient.generate_completion currently only takes a string prompt.
        # Let's combine history into a single prompt for now, or update LLMClient (better).
        full_conversation = ""
        for msg in chat_context:
            full_conversation += f"{msg['role'].capitalize()}: {msg['content']}\n"
        full_conversation += f"User: {request.message}\nAssistant:"
        
        response_text = llm.generate_completion(full_conversation, system_prompt=system_prompt)
        
        # 5. Store Assistant message
        assistant_msg = ChatHistory(session_id=session_id, role="assistant", content=response_text)
        db.add(assistant_msg)
        
        # 6. Log to audit
        from app.services.audit_service import log_action
        log_action(db, "chatbot", session_id, "chat", "success")
        
        db.commit()
        
        return ChatResponse(
            response=response_text,
            context_used=bool(latest_emails)
        )
        
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
