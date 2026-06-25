from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.settings_manager import load_settings, save_settings
from app.services.ingestion.gmail_service import GmailService
from app.auth.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    ai_model_mode: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    auto_process: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    max_daily_automations: Optional[int] = None

@router.get("/")
def get_current_settings(current_user: User = Depends(get_current_user)):
    """Retrieve current settings, including Gmail integration connection check"""
    current = load_settings()
    
    # Check Gmail Connection status
    gmail_connected = False
    try:
        # Use user-specific token JSON if available
        GmailService(token_json=current_user.gmail_token_json)
        gmail_connected = True
    except Exception:
        pass
        
    current["gmail_connected"] = gmail_connected
    return current

@router.post("/")
def update_settings(
    update_data: SettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Save new configurations and sync to memory"""
    try:
        # Convert Pydantic object to dict, ignoring unset fields
        data_to_save = update_data.model_dump(exclude_unset=True)
        updated = save_settings(data_to_save)
        return updated
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")
