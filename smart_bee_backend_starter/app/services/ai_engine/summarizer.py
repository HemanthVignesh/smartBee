"""Email Summarization"""

from app.services.ai_engine.llm_client import LLMClient


class EmailSummarizer:
    """Generate email summaries"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def summarize(self, email_body: str, max_length: int = 500) -> str:
        """Generate concise email summary"""
        system_prompt = """You are an email summarizer. Analyze the email and generate a summary with exactly three bullet points, each being a single concise sentence.
Follow this format strictly:
- **Who sent it**: [Identify the sender's name and/or organization]
- **What it is about**: [Summarize the core message or request of the email in one sentence]
- **When/Deadline**: [Specify when any deadline is, or state "None" if there is no deadline]

Do not include any introductory or concluding text. Generate only the three bullet points."""
        
        response = self.llm.generate_completion(email_body[:1000], system_prompt, max_tokens=250)
        response_text = response.strip()
        
        # Post-process response to ensure strict format adherence
        import re
        who_val = None
        what_val = None
        when_val = None
        
        # Try regex search on the generated response
        who_match = re.search(r"\*?\*?Who(?: sent it)?\*?\*?:\s*([^\n]+)", response_text, re.IGNORECASE)
        if who_match:
            who_val = who_match.group(1).strip()
            
        what_match = re.search(r"\*?\*?What(?: it is about)?\*?\*?:\s*([^\n]+)", response_text, re.IGNORECASE)
        if what_match:
            what_val = what_match.group(1).strip()
            
        when_match = re.search(r"\*?\*?(?:When/Deadline|When|Deadline)\*?\*?:\s*([^\n]+)", response_text, re.IGNORECASE)
        if when_match:
            when_val = when_match.group(1).strip()
            
        # Fallback if any parts are missing
        if not who_val or not what_val:
            # Check if response already has bullet points
            lines = [l.strip() for l in response_text.split("\n") if l.strip()]
            if len(lines) >= 3:
                # Use them directly by striping any leading bullet markers
                bullets = []
                for l in lines[:3]:
                    cleaned = re.sub(r"^[-*#\s\d\.\:]+", "", l).strip()
                    # Strip bold prefix if present e.g. "**Who sent it**: "
                    cleaned = re.sub(r"^\*?\*?[^*:]+\*?\*?:\s*", "", cleaned).strip()
                    bullets.append(cleaned)
                who_val, what_val, when_val = bullets[0], bullets[1], bullets[2]
            else:
                # Extract details from the email body
                who_val = who_val or "Unknown Sender"
                sender_match = re.search(r"(?:From|Sender):\s*([^\n]+)", email_body, re.IGNORECASE)
                if sender_match:
                    who_val = sender_match.group(1).strip()
                
                what_val = what_val or response_text
                what_val = re.sub(r"^[-*#\s\d\.\:]+", "", what_val).strip()
                
                if not when_val:
                    when_val = "None"
                    for line in email_body.split("\n"):
                        if any(k in line.lower() for k in ["deadline", "due date", "due by", "action required by"]):
                            when_val = line.strip()
                            break
                            
        # Format strictly
        return (
            f"- **Who sent it**: {who_val}\n"
            f"- **What it is about**: {what_val}\n"
            f"- **When/Deadline**: {when_val}"
        )