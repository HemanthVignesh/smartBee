"""Email Intent Detection"""

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


class IntentDetector:
    def __init__(self):
        self.llm = LLMClient()
        self.model = None
        
        # Try to load the trained ML model
        import os
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), "intent_model.joblib")
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info("Loaded trained machine learning intent model from disk.")
            except Exception as e:
                logger.error(f"Failed to load trained intent model: {e}")

    def detect(self, subject: str, body: str) -> Dict:
        # If the ML model is trained, prioritize it
        if self.model is not None:
            try:
                text_to_predict = f"Subject: {subject}\nBody: {body}"
                predicted_class = self.model.predict([text_to_predict])[0]
                
                # Check model prediction probabilities if possible, otherwise use fallback high confidence
                try:
                    probs = self.model.predict_proba([text_to_predict])[0]
                    class_idx = list(self.model.classes_).index(predicted_class)
                    confidence = float(probs[class_idx])
                except Exception:
                    confidence = 0.95
                    
                # Map the predicted label to internal system schema
                text_lower = (subject + " " + body).lower()
                
                if predicted_class == "inquiry":
                    return {
                        "intent": "question",
                        "needs_reply": True,
                        "confidence": confidence,
                        "reasoning": "Classified as inquiry by trained intent model."
                    }
                elif predicted_class == "complaint":
                    return {
                        "intent": "general",  # Treat complaints as general requiring user response
                        "needs_reply": True,
                        "confidence": confidence,
                        "reasoning": "Classified as complaint by trained intent model."
                    }
                elif predicted_class == "feedback":
                    return {
                        "intent": "informational",
                        "needs_reply": False,
                        "confidence": confidence,
                        "reasoning": "Classified as feedback by trained intent model."
                    }
                elif predicted_class == "request":
                    # Check for meeting/scheduling signals within request context
                    meeting_keywords = ["meeting", "call", "zoom", "discuss", "schedule", "calendar", "appointment"]
                    if any(k in text_lower for k in meeting_keywords):
                        return {
                            "intent": "meeting_request",
                            "needs_reply": True,
                            "confidence": confidence,
                            "reasoning": "Classified as request by trained model; scheduling keyword detected."
                        }
                    else:
                        return {
                            "intent": "task_assignment",
                            "needs_reply": True,
                            "confidence": confidence,
                            "reasoning": "Classified as request by trained intent model."
                        }
            except Exception as e:
                logger.warning(f"Trained model inference failed: {e}. Falling back to LLM.")

        system_prompt = """Classify the given email's primary intent and determine if a response or reply is required from the recipient.

Allowed Intents:
1. "meeting_request": Senders asking to schedule a meeting, call, appointment, or confirm a date/time.
2. "task_assignment": Senders assigning a task, requesting an action, or asking the recipient to perform some work.
3. "deadline_reminder": Notifications or messages reminding the recipient of an upcoming deadline, due date, or deliverable.
4. "question": Senders asking a direct question to the recipient that requires information, feedback, or a decision.
5. "general": General conversations, greetings, and generic updates.
6. "informational": Passive status reports, newsletters, automated notifications, shipping confirmations, receipts, and other one-way info transfers.

Determining "needs_reply":
Set "needs_reply" to true if:
- The email has a direct question to the recipient.
- The email explicitly asks for a reply, confirmation, decision, feedback, or action from the recipient.
- The email requests scheduling or attending a meeting.
Set "needs_reply" to false if:
- The email is purely informational, an automated alert, status report, generic receipt, newsletters, advertisements, spam, or a one-way notification where no reply is expected or necessary.

Return ONLY a valid JSON object matching the schema below (do not include other text):
{
    "intent": "meeting_request|task_assignment|deadline_reminder|question|general|informational",
    "needs_reply": true,
    "confidence": 0.95,
    "reasoning": "A concise explanation of the detected intent and why a reply is or isn't needed."
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
            logger.warning(f"Intent detection failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.6,
                "reasoning": "fallback"
            }


_intent_detector = IntentDetector()

def detect_intent(subject: str, body: str) -> Dict:
    return _intent_detector.detect(subject, body)
