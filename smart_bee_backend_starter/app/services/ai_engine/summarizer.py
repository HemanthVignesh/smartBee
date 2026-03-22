"""Email Summarization"""

from app.services.ai_engine.llm_client import LLMClient


class EmailSummarizer:
    """Generate email summaries"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def summarize(self, email_body: str, max_length: int = 100) -> str:
        """Generate concise email summary"""
        system_prompt = f"""Summarize the email in {max_length} characters or less.
Focus on: who, what, when, where, why.
Be concise and actionable."""
        
        response = self.llm.generate_completion(email_body[:1000], system_prompt)
        return response[:max_length]