"""LLM Client for AI Processing"""

from typing import Dict, Optional
import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-engine (Gemini, OpenAI, Local HF Transformer) LLM Client with offline fallback"""
    
    def __init__(self):
        self.openai_client = None

    def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """Generate completion dynamically using settings configured model mode with fallback chain"""
        from app.services.settings_manager import load_settings
        app_settings = load_settings()
        preferred_mode = app_settings.get("ai_model_mode", "local")
        
        # Build fallback execution order
        if preferred_mode == "gemini":
            chain = ["gemini", "openai", "local", "offline_mock"]
        elif preferred_mode == "openai":
            chain = ["openai", "gemini", "local", "offline_mock"]
        elif preferred_mode == "local":
            chain = ["local", "gemini", "openai", "offline_mock"]
        elif preferred_mode == "offline_mock":
            chain = ["offline_mock", "gemini", "openai", "local"]
        else:
            chain = ["local", "gemini", "openai", "offline_mock"]
            
        print(f"🤖 LLM waterfall execution chain: {chain} (Preferred: {preferred_mode})")
        
        for mode in chain:
            # 1. Google Gemini API Mode
            if mode == "gemini":
                gemini_key = app_settings.get("gemini_api_key") or settings.GEMINI_API_KEY
                if not gemini_key:
                    print("🤖 Skipping Gemini in fallback chain: API key not set")
                    continue
                try:
                    settings.GEMINI_API_KEY = gemini_key
                    print("🤖 Attempting generation with Gemini...")
                    res = self._generate_gemini(prompt, system_prompt, max_tokens)
                    print(f"🤖 Gemini generation succeeded! Output: {repr(res)}")
                    return res
                except Exception as e:
                    print(f"🤖 Gemini generation failed: {e}. Trying next fallback...")
                    
            # 2. OpenAI API Mode
            elif mode == "openai":
                openai_key = app_settings.get("openai_api_key") or settings.OPENAI_API_KEY
                if not openai_key:
                    print("🤖 Skipping OpenAI in fallback chain: API key not set")
                    continue
                try:
                    settings.OPENAI_API_KEY = openai_key
                    if not self.openai_client or self.openai_client.api_key != openai_key:
                        self.openai_client = openai.OpenAI(api_key=openai_key)
                    print("🤖 Attempting generation with OpenAI...")
                    res = self._generate_openai(prompt, system_prompt, max_tokens)
                    print(f"🤖 OpenAI generation succeeded! Output: {repr(res)}")
                    return res
                except Exception as e:
                    print(f"🤖 OpenAI generation failed: {e}. Trying next fallback...")
                    
            # 3. Local Offline Transformer Model Mode
            elif mode == "local":
                try:
                    # Bypass heavy transformer for classification tasks if ML models are available
                    is_category_req = "category" in prompt.lower() or (system_prompt and "category" in system_prompt.lower())
                    is_intent_req = "intent" in prompt.lower() or (system_prompt and "intent" in system_prompt.lower())
                    
                    if is_category_req:
                        import os
                        import joblib
                        model_path = os.path.join(os.path.dirname(__file__), "category_model.joblib")
                        if os.path.exists(model_path):
                            print("🤖 Local ML bypass: using category_model.joblib for classification")
                            model = joblib.load(model_path)
                            predicted_class = model.predict([prompt])[0]
                            try:
                                probs = model.predict_proba([prompt])[0]
                                class_idx = list(model.classes_).index(predicted_class)
                                confidence = float(probs[class_idx])
                            except Exception:
                                confidence = 0.95
                            return f'{{"category": "{predicted_class}", "confidence": {confidence:.2f}, "reasoning": "Classified by trained ML category model local bypass."}}'
                            
                    if is_intent_req:
                        import os
                        import joblib
                        model_path = os.path.join(os.path.dirname(__file__), "intent_model.joblib")
                        if os.path.exists(model_path):
                            print("🤖 Local ML bypass: using intent_model.joblib for classification")
                            model = joblib.load(model_path)
                            predicted_class = model.predict([prompt])[0]
                            try:
                                probs = model.predict_proba([prompt])[0]
                                class_idx = list(model.classes_).index(predicted_class)
                                confidence = float(probs[class_idx])
                            except Exception:
                                confidence = 0.95
                                
                            # Map predicted_class to JSON matching the expected output schema
                            text_lower = prompt.lower()
                            needs_reply = False
                            if predicted_class in ["inquiry", "complaint", "request"]:
                                needs_reply = True
                                
                            mapped_intent = "general"
                            if predicted_class == "inquiry":
                                mapped_intent = "question"
                            elif predicted_class == "feedback":
                                mapped_intent = "informational"
                                needs_reply = False
                            elif predicted_class == "request":
                                meeting_keywords = ["meeting", "call", "zoom", "discuss", "schedule", "calendar", "appointment"]
                                if any(k in text_lower for k in meeting_keywords):
                                    mapped_intent = "meeting_request"
                                else:
                                    mapped_intent = "task_assignment"
                                    
                            return f'{{"intent": "{mapped_intent}", "needs_reply": {str(needs_reply).lower()}, "confidence": {confidence:.2f}, "reasoning": "Classified by trained ML intent model local bypass."}}'

                    from app.services.ai_engine.local_transformer import LocalTransformerClient
                    local_client = LocalTransformerClient()
                    
                    # Format prompts clearly for Flan-T5/Qwen instruction tuning format
                    combined_prompt = ""
                    if system_prompt:
                        combined_prompt += f"{system_prompt}\n"
                    combined_prompt += f"{prompt}"
                    
                    print("🤖 Attempting generation with Local Transformer...")
                    res = local_client.generate(combined_prompt, max_new_tokens=max_tokens)
                    print(f"🤖 Local Transformer generation succeeded! Output: {repr(res)}")
                    return res
                except Exception as e:
                    print(f"🤖 Local transformer generation failed: {e}. Trying next fallback...")
                    
            # 4. Fall back to smart offline mockup
            elif mode == "offline_mock":
                print("🤖 Attempting generation with Offline Mock...")
                res = self._generate_offline_mock(prompt, system_prompt, max_tokens)
                print(f"🤖 Offline Mock generation succeeded! Output: {repr(res)}")
                return res
                
        # Absolute fallback if somehow the chain finishes without returning
        print("🤖 Absolute fallback to Offline Mock...")
        res = self._generate_offline_mock(prompt, system_prompt, max_tokens)
        print(f"🤖 Offline Mock generation succeeded! Output: {repr(res)}")
        return res

    def _generate_gemini(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """Call Google Gemini API using HTTP POST. Raises exception on failure."""
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        
        contents = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        if system_prompt:
            contents["systemInstruction"] = {
                "parts": [
                    {"text": system_prompt}
                ]
            }
            
        # Optimize output for JSON if requested
        generation_config = {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7
        }
        if "json" in prompt.lower() or (system_prompt and "json" in system_prompt.lower()):
            generation_config["responseMimeType"] = "application/json"
            
        contents["generationConfig"] = generation_config
        
        r = httpx.post(url, json=contents, timeout=5.0)
        r.raise_for_status()
        data = r.json()
        if "candidates" not in data or not data["candidates"]:
            raise RuntimeError(f"Gemini API returned no candidates: {data}")
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text

    def _generate_openai(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """Generate completion using OpenAI Chat Completions. Raises exception on failure."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        model_name = settings.OPENAI_MODEL
        if model_name.lower() in ["gpt-5", "gpt5"]:
            print("🤖 OpenAI mapping: 'gpt-5' detected. Proxying to 'gpt-4o' for live API execution.")
            model_name = "gpt-4o"
            
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=5.0
        )
        return response.choices[0].message.content

    def _generate_offline_mock(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """Deterministic mockup parsing if keys are not present or APIs fail"""
        
        # Check if looking for category classification
        if "category" in prompt.lower() or (system_prompt and "category" in system_prompt.lower()):
            import os
            import joblib
            model_path = os.path.join(os.path.dirname(__file__), "category_model.joblib")
            if os.path.exists(model_path):
                try:
                    model = joblib.load(model_path)
                    predicted_class = model.predict([prompt])[0]
                    try:
                        probs = model.predict_proba([prompt])[0]
                        class_idx = list(model.classes_).index(predicted_class)
                        confidence = float(probs[class_idx])
                    except Exception:
                        confidence = 0.95
                    return f'{{"category": "{predicted_class}", "confidence": {confidence:.2f}, "reasoning": "Classified by trained ML category model offline fallback."}}'
                except Exception as e:
                    logger.warning(f"Offline model inference failed: {e}")
                    
            prompt_lower = prompt.lower()
            if any(k in prompt_lower for k in ["facebook", "linkedin", "twitter", "instagram", "social"]):
                return '{"category": "social", "confidence": 0.95, "reasoning": "Social keyword match"}'
            elif any(k in prompt_lower for k in ["promo", "offer", "discount", "newsletter", "sale", "shop", "ajio", "luxe"]):
                return '{"category": "promotions", "confidence": 0.9, "reasoning": "Promotions keyword match"}'
            elif any(k in prompt_lower for k in ["alert", "invoice", "receipt", "bill", "payment", "bank", "statement", "confirm"]):
                return '{"category": "updates", "confidence": 0.95, "reasoning": "Updates keyword match"}'
            else:
                return '{"category": "primary", "confidence": 0.8, "reasoning": "Default category fallback"}'
        
        # Check if looking for intent classification
        if "intent" in prompt.lower() or (system_prompt and "intent" in system_prompt.lower()):
            import re
            body_lower = prompt.lower()
            subject_lower = prompt.split("Body:")[0].lower() if "Body:" in prompt else prompt.lower()
            
            def _has_word(text: str, words: list) -> bool:
                return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)
            
            # Meeting request
            if _has_word(body_lower, ["meeting", "call", "zoom", "discuss", "schedule"]) or _has_word(subject_lower, ["meeting", "call", "zoom", "discuss", "schedule"]):
                return '{"intent": "meeting_request", "needs_reply": true, "confidence": 0.95, "reasoning": "Keyword matching: found meeting scheduling signals."}'
            
            # Direct Question
            elif "?" in body_lower or _has_word(body_lower, ["question", "ask", "let me know", "reply", "respond"]):
                return '{"intent": "question", "needs_reply": true, "confidence": 0.9, "reasoning": "Keyword matching: found question marks or reply request signals."}'
            
            # Task assignment
            elif _has_word(body_lower, ["deadline", "due", "assign", "deliverable", "action item"]):
                return '{"intent": "task_assignment", "needs_reply": false, "confidence": 0.85, "reasoning": "Keyword matching: found task assignment signals without direct reply expectation."}'
                
            # Informational / Status report
            elif _has_word(body_lower, ["completed", "status", "update", "pushed", "no action"]):
                return '{"intent": "informational", "needs_reply": false, "confidence": 0.9, "reasoning": "Keyword matching: found status update signals with no action expected."}'
                
            else:
                return '{"intent": "general", "needs_reply": false, "confidence": 0.7, "reasoning": "Default intent detection fallback."}'
        
        # Check if looking for entity extraction
        if "entities" in prompt.lower() or (system_prompt and "entities" in system_prompt.lower()):
            import re
            import json
            dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b", prompt)
            times = re.findall(r"\b\d{1,2}:\d{2}\b|\b\d{1,2}\s?(?:am|pm|AM|PM)\b", prompt)
            return json.dumps({
                "dates": list(set(dates)),
                "times": list(set(times)),
                "people": [],
                "locations": [],
                "keywords": []
            })
            
        # Check if looking for summary
        if "summarize" in prompt.lower() or (system_prompt and "summarize" in system_prompt.lower()):
            import re
            
            # Try to find Sender
            sender = "Unknown Sender"
            sender_match = re.search(r"(?:From|Sender):\s*([^\n]+)", prompt, re.IGNORECASE)
            if sender_match:
                sender = sender_match.group(1).strip()
            
            # Try to find Subject
            subject = ""
            subject_match = re.search(r"Subject:\s*([^\n]+)", prompt, re.IGNORECASE)
            if subject_match:
                subject = subject_match.group(1).strip()
            
            # Try to find a line from the body to represent what it is about
            body_line = ""
            lines = [line.strip() for line in prompt.split("\n") if line.strip()]
            for l in lines:
                l_lower = l.lower()
                if any(l_lower.startswith(p) for p in ["subject:", "original email:", "body:", "context:", "from:", "sender:", "recipient:"]):
                    continue
                if any(l_lower.startswith(g) for g in ["dear", "hi", "hello", "hey"]):
                    continue
                if len(l) < 15 or any(l_lower.startswith(s) for s in ["best regards", "thanks", "sincerely", "regards"]):
                    continue
                body_line = l
                break
            
            if not body_line:
                body_line = f"This email is regarding '{subject}'." if subject else "This email contains general info or requests."
            else:
                body_line = body_line[:120].strip()
                if not body_line.endswith("."):
                    body_line += "."
            
            # Try to find a date or deadline
            deadline = "None"
            for line in lines:
                if any(k in line.lower() for k in ["deadline", "due date", "due by", "action required by"]):
                    deadline = line.strip()
                    break
            
            if deadline == "None":
                deadline_match = re.search(r"(?:deadline|due|by|before|date):\s*([^\n\.]+)", prompt, re.IGNORECASE)
                if deadline_match:
                    deadline = deadline_match.group(1).strip()
                else:
                    date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b", prompt)
                    if date_match:
                        deadline = f"Deliverable or update by {date_match.group(0)}."

            return (
                f"- **Who sent it**: {sender}\n"
                f"- **What it is about**: {body_line}\n"
                f"- **When/Deadline**: {deadline}"
            )
            
        # Chatbot response fallbacks
        body_lower = prompt.lower()
        if "inbox" in body_lower or "summarize" in body_lower or "emails" in body_lower:
            return "I can help you with your inbox! Once your Gmail is synced, I'll be able to summarize your latest emails, highlight priorities, and suggest actions for you."
        elif "meeting" in body_lower or "schedule" in body_lower:
            return "I can help schedule meetings! Once emails are synced from Gmail, I'll automatically detect meeting requests and suggest calendar events."
        else:
            return "Hi there! I'm your Smart Bee AI assistant. I'm currently running without an active API key. You can ask me to summarize your inbox, check scheduled actions, or help with email replies once Gmail is connected."