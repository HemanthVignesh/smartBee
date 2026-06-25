# Monkeypatch importlib.metadata to prevent slow filesystem scanning/crawling which hangs Pydantic/Uvicorn startup on macOS
import importlib.metadata

class MockEntryPoints(tuple):
    def select(self, *args, **kwargs):
        return MockEntryPoints()

importlib.metadata.distributions = lambda *args, **kwargs: []
importlib.metadata.entry_points = lambda *args, **kwargs: MockEntryPoints()

# Configuration loader — UPDATED for JWT Auth + Google OAuth
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "Smart BEE"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./smartbee.db"

    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_TOKEN_FILE: str = "token.pickle"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    FRONTEND_URL: str = "http://localhost:5173"

    # ── JWT ──────────────────────────────────────────────────────────────────
    # Generate a strong secret with:  python -c "import secrets; print(secrets.token_hex(32))"
    # Must be at least 32 random characters.  NEVER commit the real value.
    JWT_SECRET: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET_BEFORE_DEPLOYING"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── Google OAuth 2.0 ─────────────────────────────────────────────────────
    # Create credentials at https://console.cloud.google.com → APIs & Services → Credentials
    # Authorised redirect URI must be set to exactly:  {BACKEND_URL}/api/v1/auth/google/callback
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
