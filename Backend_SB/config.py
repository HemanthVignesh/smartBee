"""
SmartBee — Typed configuration loaded from environment / .env file.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Database ─────────────────────────────────
    # SQLite for local dev, PostgreSQL for production.
    # Dev:  sqlite+aiosqlite:///./smartbee.db
    # Prod: postgresql+asyncpg://user:pass@host:5432/smartbee
    DATABASE_URL: str = "sqlite+aiosqlite:///./smartbee.db"

    # ── AI keys (server-side only, never sent to frontend) ──
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ── Security ─────────────────────────────────
    SECRET_KEY: str = "change-me-generate-a-real-secret"

    # ── Brain thresholds ─────────────────────────
    CONFIDENCE_THRESHOLD_HIGH: float = 0.8
    CONFIDENCE_THRESHOLD_MEDIUM: float = 0.6

    # ── Scheduler ────────────────────────────────
    DEFAULT_REMINDER_OFFSET_MINUTES: int = 30

    # ── Rate limiting ────────────────────────────
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_GENERAL: int = 60
    RATE_LIMIT_AI: int = 10
    RATE_LIMIT_SENSITIVE: int = 5

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
