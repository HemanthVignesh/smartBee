"""Email Intent Detection"""

from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class IntentDetector:
    def __init__(self):
        self.llm = LLMClient()

    def detect(self, subject: str, body: str) -> Dict:
        system_prompt = """Classify email intent.

Return ONLY JSON:
{
    "intent": "meeting_request|task_assignment|deadline_reminder|general",
    "confidence": 0.85,
    "reasoning": "short explanation"
}
"""

        prompt = f"""Subject: {subject}
Body:
{body[:500]}
"""

        try:
            response = self.llm.generate_completion(prompt, system_prompt)
            import json
            return json.loads(response)
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.6,
                "reasoning": "fallback"
            }


_intent_detector = IntentDetector()

def detect_intent(subject: str, body: str) -> Dict:
    return _intent_detector.detect(subject, body)
