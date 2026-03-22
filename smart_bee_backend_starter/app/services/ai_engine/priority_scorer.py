"""Email Priority Scoring"""

from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class PriorityScorer:
    def __init__(self):
        self.llm = LLMClient()

    def score(self, email_text: str, intent: str) -> str:
        """Score email priority based on text and detected intent"""
        system_prompt = """Score email priority based on the email content and intent.

Return ONLY JSON:
{
    "priority": "high",
    "score": 0.85,
    "factors": ["urgent keyword", "from important sender"]
}
"""

        prompt = f"""Email text: {email_text[:300]}
Detected intent: {intent}

Determine priority level (high/medium/low)."""

        try:
            response = self.llm.generate_completion(prompt, system_prompt)
            import json
            result = json.loads(response)
            return result.get("priority", "medium")
        except Exception as e:
            logger.warning(f"Priority scoring failed: {e}")
            # Fallback based on intent
            if intent in ["deadline_reminder", "urgent"]:
                return "high"
            elif intent in ["meeting_request", "task_assignment"]:
                return "medium"
            else:
                return "low"


# ✅ MODULE-LEVEL SINGLETON AND EXPORT FUNCTION
_priority_scorer = PriorityScorer()

def score_priority(email_text: str, intent: str) -> str:
    """Module-level function that matches main.py's call"""
    return _priority_scorer.score(email_text, intent)