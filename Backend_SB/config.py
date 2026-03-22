"""
Global configuration for Smart Bee Backend
"""

from pathlib import Path

# -------------------------
# App Settings
# -------------------------

APP_NAME = "Smart Bee"
APP_ENV = "development"  # development | production
DEBUG = True

# -------------------------
# Database (for later use)
# -------------------------

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "smartbee.db"

# -------------------------
# AI Settings
# -------------------------

CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6

# -------------------------
# Scheduler Defaults
# -------------------------

DEFAULT_REMINDER_OFFSET_MINUTES = 30

