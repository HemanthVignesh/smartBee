"""
SmartBee — /api/v1/settings  router
────────────────────────────────────
GET  /api/v1/settings/         → returns masked key status + other settings
POST /api/v1/settings/         → accepts new settings; stores keys securely
DELETE /api/v1/settings/keys/{provider}  → removes a stored key
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...security.keys import get_key_status, store_key, delete_key
from ...config import settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SettingsUpdateRequest(BaseModel):
    ai_model_mode: str = "local"
    # Raw key values — optional; empty string = "no change"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    auto_process: bool = True
    confidence_threshold: float = 0.8
    max_daily_automations: int = 50


class SettingsResponse(BaseModel):
    ai_model_mode: str
    # Key status — NEVER the actual key
    gemini_key_status: dict
    openai_key_status: dict
    auto_process: bool
    confidence_threshold: float
    max_daily_automations: int
    debug: bool


# ─── In-memory non-secret settings store (swap for DB row in production) ──────
_runtime_settings: dict = {
    "ai_model_mode": "local",
    "auto_process": True,
    "confidence_threshold": 0.8,
    "max_daily_automations": 50,
}


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=SettingsResponse)
def get_settings():
    """Return current settings.  Keys are masked — never full values."""
    return SettingsResponse(
        ai_model_mode=_runtime_settings["ai_model_mode"],
        gemini_key_status=get_key_status("gemini"),
        openai_key_status=get_key_status("openai"),
        auto_process=_runtime_settings["auto_process"],
        confidence_threshold=_runtime_settings["confidence_threshold"],
        max_daily_automations=_runtime_settings["max_daily_automations"],
        debug=settings.DEBUG,
    )


@router.post("/")
def update_settings(body: SettingsUpdateRequest):
    """
    Save settings.  If a key field is provided and non-empty, encrypt and store it.
    Keys that are already masked (contain '•') are ignored — the frontend
    should send empty string when the user hasn't changed the key.
    """
    # Update non-secret settings in memory
    _runtime_settings["ai_model_mode"] = body.ai_model_mode
    _runtime_settings["auto_process"] = body.auto_process
    _runtime_settings["confidence_threshold"] = body.confidence_threshold
    _runtime_settings["max_daily_automations"] = body.max_daily_automations

    # Store keys securely if the user provided new values
    errors = []

    if body.gemini_api_key and "•" not in body.gemini_api_key:
        try:
            store_key("gemini", body.gemini_api_key)
        except ValueError as e:
            errors.append(str(e))

    if body.openai_api_key and "•" not in body.openai_api_key:
        try:
            store_key("openai", body.openai_api_key)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    return {
        "status": "ok",
        "message": "Settings saved.",
        "gemini_key_status": get_key_status("gemini"),
        "openai_key_status": get_key_status("openai"),
    }


@router.delete("/keys/{provider}")
def remove_key(provider: str):
    """Delete a stored API key from the database."""
    if provider not in ("gemini", "openai"):
        raise HTTPException(status_code=400, detail="Unknown provider. Use 'gemini' or 'openai'.")
    delete_key(provider)
    return {"status": "ok", "message": f"{provider} key removed."}
