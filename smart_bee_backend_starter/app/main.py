# Monkeypatch importlib.metadata to prevent slow filesystem scanning/crawling which hangs Pydantic/Uvicorn startup on macOS
import importlib.metadata
importlib.metadata.distributions = lambda *args, **kwargs: []
importlib.metadata.entry_points = lambda *args, **kwargs: {}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.api.v1 import router as api_router

# Import models to ensure they're registered
import app.models

from app.services.scheduler import start_scheduler_thread

logger = logging.getLogger(__name__)


def _initial_gmail_sync():
    """Attempt to fetch real emails from Gmail on startup. Gracefully skips if Gmail isn't configured."""
    try:
        from app.services.ingestion.email_ingestor import EmailIngestor
        db = SessionLocal()
        try:
            ingestor = EmailIngestor(db)
            if ingestor.gmail.mock_mode:
                print("⚠️  Gmail not configured — running without inbox sync. Configure OAuth credentials to enable real email data.")
                return
            saved = ingestor.fetch_and_store_unread(max_results=20)
            print(f"✅ Initial Gmail sync: fetched and stored {len(saved)} new email(s).")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Startup Gmail sync failed (non-fatal): {e}")
        print(f"⚠️  Startup Gmail sync skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # 1. Create DB tables first (must complete before any writes)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # 2. Database migrations (add category column if not present)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE emails ADD COLUMN category VARCHAR DEFAULT 'primary';"))
            print("✅ Database migration: added 'category' column to 'emails' table")
    except Exception as e:
        # Suppress error if the column already exists
        pass

    # 2. Start background threads (non-blocking)
    import threading
    # Initial Gmail sync runs in background after a short delay to let DB settle
    sync_thread = threading.Thread(
        target=lambda: (__import__("time").sleep(2), _initial_gmail_sync()),
        daemon=True
    )
    sync_thread.start()

    # 3. Start scheduler (also runs in background)
    start_scheduler_thread()

    yield
    # Shutdown
    print("👋 Shutting down Smart BEE")

# Create FastAPI app
app = FastAPI(
    title="Smart BEE Backend",
    description="AI-Powered Email Intelligence Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router.router, prefix="/api/v1")

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Smart BEE Backend is running 🐝",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to Smart BEE API",
        "docs": "/docs",
        "health": "/health"
    }