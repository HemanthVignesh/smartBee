# Configuration loader
from pydantic_settings import BaseSettings
from typing import Optional

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
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()