def decide_action(analysis: dict) -> dict | None:
    """
    Convert analysis into a suggested action.
    Returns None if no action is required.
    """

    intent = analysis["intent"]
    priority = analysis["priority"]
    entities = analysis.get("entities", {})

    # --- Meeting request ---
    if intent == "meeting_request" and priority == "high":
        if "date" in entities and "time" in entities:
            return {
                "action_type": "create_calendar_event",
                "payload": {
                    "title": "Meeting Request",
                    "date": entities["date"],
                    "time": entities["time"]
                }
            }

    # --- Deadline / task ---
    if intent == "deadline_task" and "date" in entities:
        return {
            "action_type": "create_reminder",
            "payload": {
                "date": entities["date"],
                "note": "Task deadline reminder"
            }
        }

    # --- Default ---
    return None
