from datetime import datetime, timezone


def now_iso() -> str:
    """
    Returns current UTC time as ISO 8601 string (timezone-aware).
    """
    return datetime.now(timezone.utc).isoformat()
