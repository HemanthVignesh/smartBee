from app.services.ai_engine.intent_detector import detect_intent
from app.services.ai_engine.priority_scorer import score_priority
from app.services.ai_engine.entity_extractor import extract_entities
from app.services.ai_engine.reply_generator import generate_replies


def analyze_email(email) -> dict:
    """
    Core AI brain for Smart BEE
    """

    body = email.body

    # 1️⃣ Intent detection
    intent_result = detect_intent(body)

    # 2️⃣ Priority scoring
    priority = score_priority(body, intent_result["intent"])

    # 3️⃣ Entity extraction
    entities = extract_entities(body)

    analysis = {
        "intent": intent_result["intent"],
        "confidence": intent_result["confidence"],
        "priority": priority,
        "entities": entities,
        "summary": body[:120] + "..."
    }
    if "can you" in email.body.lower() or "please" in email.body.lower():
        analysis["intent"] = "reply_required"
        analysis["replies"] = generate_replies(email.body)


    # 4️⃣ Smart Replies (conditional)
    if intent_result["intent"] == "reply_required":
        analysis["replies"] = generate_replies(body)

    return analysis
