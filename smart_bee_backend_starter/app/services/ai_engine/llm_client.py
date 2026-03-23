"""LLM Client for AI Processing"""

from typing import Dict, Optional
import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI client for Smart BEE (v1.x compat)"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured")
    
    def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """Generate completion using OpenAI Chat Completions"""
        if not self.client:
            return "OpenAI API key not configured"
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error: {str(e)}"