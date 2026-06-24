"""Email Categorization Service"""

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


class EmailCategorizer:
    def __init__(self):
        self.llm = LLMClient()
        self.model = None
        
        # Load local ML category model if it exists
        import os
        import joblib
        model_path = os.path.join(os.path.dirname(__file__), "category_model.joblib")
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info("Loaded trained machine learning category model from disk.")
            except Exception as e:
                logger.error(f"Failed to load trained category model: {e}")

    def categorize(self, subject: str, body: str, sender: str) -> str:
        # 1. If ML category model is available, use it first or as a high-confidence local predictor
        if self.model is not None:
            try:
                text_to_predict = f"Sender: {sender}\nSubject: {subject}\nBody: {body}"
                predicted_class = self.model.predict([text_to_predict])[0]
                
                # Check confidence/probability
                try:
                    probs = self.model.predict_proba([text_to_predict])[0]
                    class_idx = list(self.model.classes_).index(predicted_class)
                    confidence = float(probs[class_idx])
                except Exception:
                    confidence = 0.95
                
                logger.info(f"Local ML model prediction for '{subject[:30]}': {predicted_class} (confidence: {confidence:.2f})")
                
                # Retrieve current preferred AI mode
                from app.services.settings_manager import load_settings
                app_settings = load_settings()
                preferred_mode = app_settings.get("ai_model_mode", "local")
                
                # Use model directly if local mode is preferred or if confidence is high (>= 0.5)
                if preferred_mode in ["local", "offline_mock"] or confidence >= 0.5:
                    if predicted_class in ["primary", "promotions", "social", "updates", "forums"]:
                        return predicted_class
            except Exception as e:
                logger.warning(f"Trained category model inference failed: {e}. Falling back to LLM waterfall.")

        system_prompt = """Classify the given email into exactly one of the five categories below.

Allowed Categories:
1. "primary": Personal or one-on-one conversations, direct messages/replies from colleagues, managers, friends, family, direct questions/requests from people, client communications, work assignments, and important emails requiring individual human attention or replies.
2. "promotions": Marketing emails, advertisements, discount offers, newsletter subscriptions, recommendations, deals, sales announcements, product pitches, coupon codes, shopping offers, and mass marketing campaigns. Note that automated job recommendation digests (e.g. from Naukri, foundit) and marketing digests are PROMOTIONS.
3. "social": Notifications, messages, and alerts from social networks, professional networks, dating services, or community sites (e.g. LinkedIn updates, Facebook timeline alerts, Twitter follows, Instagram alerts, GitHub social activity).
4. "updates": Transactional messages, automated receipts, bills, invoices, order confirmations, shipping/delivery notifications, password resets, security alerts, service/account updates, system alerts, daily/weekly automated status reports, bank statements, tax alerts, and other one-way transactional notifications.
5. "forums": Messages from online discussion boards, mailing lists, newsgroups, Q&A forums (e.g. StackOverflow, Google Groups, GitHub discussions), and group discussion threads.

Return ONLY a valid JSON object matching the schema below (do not include other text):
{
    "category": "primary|promotions|social|updates|forums",
    "confidence": 0.95,
    "reasoning": "A concise explanation of why the email belongs in this category."
}
"""

        prompt = f"""Sender: {sender}
Subject: {subject}
Body:
{body[:500]}
"""

        try:
            response = self.llm.generate_completion(prompt, system_prompt)
            data = _parse_json(response)
            category = data.get("category", "primary").lower()
            if category in ["primary", "promotions", "social", "updates", "forums"]:
                return category
            return "primary"
        except Exception as e:
            logger.warning(f"Email categorization failed: {e}")
            return self._offline_fallback_check(subject, body, sender)

    def _offline_fallback_check(self, subject: str, body: str, sender: str) -> str:
        """Smarter offline keyword fallback logic, utilizing trained ML model if available"""
        if self.model is not None:
            try:
                text_to_predict = f"Sender: {sender}\nSubject: {subject}\nBody: {body}"
                predicted_class = self.model.predict([text_to_predict])[0]
                logger.info(f"Using trained ML category model fallback: {predicted_class}")
                if predicted_class in ["primary", "promotions", "social", "updates", "forums"]:
                    return predicted_class
            except Exception as e:
                logger.warning(f"Trained category model fallback prediction failed: {e}")

        sender_lower = sender.lower()
        body_lower = body.lower()
        subject_lower = subject.lower() if subject else ""

        # Social networks
        if any(k in sender_lower or k in body_lower or k in subject_lower for k in ["facebook", "linkedin", "twitter", "instagram", "social", "close_friend"]):
            return "social"
            
        # Promotions / Newsletters / Job Boards
        if any(k in sender_lower or k in subject_lower or k in body_lower for k in ["promo", "offer", "discount", "newsletter", "sale", "shop", "ajio", "mailer", "subscribe", "recommendation", "naukri", "monster", "foundit", "luxe", "coupon", "deal"]):
            return "promotions"
            
        # Updates / Bills / Receipts / Notifications / System Alerts
        if any(k in sender_lower or k in subject_lower or k in body_lower for k in ["alert", "invoice", "receipt", "bill", "payment", "bank", "statement", "confirm", "security", "notification", "noreply", "no-reply", "update", "digest", "status"]):
            return "updates"
            
        # Forums / Discussion
        if any(k in sender_lower or k in subject_lower or k in body_lower for k in ["forum", "discussion", "group", "mailinglist", "stackoverflow", "googlegroups"]):
            return "forums"
        
        return "primary"


_categorizer = EmailCategorizer()

def categorize_email(subject: str, body: str, sender: str) -> str:
    return _categorizer.categorize(subject, body, sender)
