"""Email Entity Extraction"""

from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract structured entities from email text"""

    def __init__(self):
        self.llm = LLMClient()

    def extract(self, subject: str, body: str) -> Dict:
        system_prompt = """Extract entities from the email.

Return ONLY valid JSON:
{
    "dates": [],
    "times": [],
    "people": [],
    "locations": [],
    "keywords": []
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
            logger.warning(f"Entity extraction failed: {e}")
            return {
                "dates": [],
                "times": [],
                "people": [],
                "locations": [],
                "keywords": []
            }


# ✅ MODULE-LEVEL SINGLETON + EXPORT (CRITICAL)
_entity_extractor = EntityExtractor()

def extract_entities(subject: str, body: str) -> Dict:
    return _entity_extractor.extract(subject, body)
