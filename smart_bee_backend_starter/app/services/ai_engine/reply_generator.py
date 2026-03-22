"""Email Reply Generator"""

from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ReplyGenerator:
    """Generate suggested email replies"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def generate(self, email_text: str, intent: str, priority: str, entities: Dict) -> str:
        """Generate a suggested reply based on email analysis"""
        system_prompt = f"""Generate a professional email reply.

Context:
- Intent: {intent}
- Priority: {priority}
- Entities: {entities}

Generate a short, professional response (2-3 sentences)."""

        prompt = f"""Original email:
{email_text[:300]}

Generate an appropriate reply."""

        try:
            response = self.llm.generate_completion(prompt, system_prompt)
            return response
        except Exception as e:
            logger.warning(f"Reply generation failed: {e}")
            # Fallback based on intent
            if intent == "meeting_request":
                return "Thank you for reaching out. I'd be happy to meet. Please let me know what times work best for you."
            elif intent == "task_assignment":
                return "I acknowledge receipt of this task and will begin work on it shortly. I'll keep you updated on my progress."
            elif intent == "deadline_reminder":
                return "Thank you for the reminder. I'm on track to meet the deadline and will deliver as scheduled."
            elif intent == "question":
                return "Thank you for your question. Let me look into this and get back to you with a detailed response."
            else:
                return "Thank you for your email. I've received your message and will respond accordingly."


# ✅ MODULE-LEVEL SINGLETON AND EXPORT FUNCTION
_reply_generator = ReplyGenerator()

def generate_replies(email_text: str, intent: str, priority: str, entities: Dict) -> str:
    """Module-level function that matches main.py's call"""
    return _reply_generator.generate(email_text, intent, priority, entities)