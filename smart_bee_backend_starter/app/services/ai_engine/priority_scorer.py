"""Email Priority Scoring"""

import re
import json
from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> dict:
    """Robustly parse JSON from LLM output, stripping markdown code fences."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text.strip())


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
            result = _parse_json(response)
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