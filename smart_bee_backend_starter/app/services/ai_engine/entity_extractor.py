"""Email Entity Extraction"""

import re
import json
from typing import Dict
import logging
from app.services.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> dict:
    """Robustly parse JSON from LLM output, stripping markdown code fences."""
    # Strip ```json ... ``` or ``` ... ``` wrappers
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text.strip())


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
            return _parse_json(response)
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
