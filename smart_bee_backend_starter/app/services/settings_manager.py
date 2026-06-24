import os
import json
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "config", 
    "smartbee_settings.json"
)

DEFAULT_SETTINGS = {
    "ai_model_mode": "local",
    "gemini_api_key": "",
    "openai_api_key": "",
    "auto_process": True,
    "confidence_threshold": 0.8,
    "max_daily_automations": 50
}

def load_settings() -> Dict[str, Any]:
    """Load settings from JSON, fallback to environment/defaults if not exists"""
    current_settings = DEFAULT_SETTINGS.copy()
    
    # Check if file exists
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                current_settings.update(saved)
        except Exception as e:
            logger.error(f"Failed to load settings file: {e}")
            
    # Sync with current settings object if keys are set in config or env
    if settings.GEMINI_API_KEY and not current_settings["gemini_api_key"]:
        current_settings["gemini_api_key"] = settings.GEMINI_API_KEY
    if settings.OPENAI_API_KEY and not current_settings["openai_api_key"]:
        current_settings["openai_api_key"] = settings.OPENAI_API_KEY
        
    # Keep the user's configured preferred mode (e.g., local)
    # and do not override it based on the presence of API keys
    pass
            
    return current_settings

def save_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Save settings to JSON and update global settings in-memory variables"""
    current = load_settings()
    current.update(new_settings)
    
    # Ensure folder exists
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        
    # Sync settings variables in memory dynamically
    settings.GEMINI_API_KEY = current.get("gemini_api_key", "")
    settings.OPENAI_API_KEY = current.get("openai_api_key", "")
    
    return current
