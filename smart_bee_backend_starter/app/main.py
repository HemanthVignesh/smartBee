from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.base import Base
from app.db.session import engine
from app.api.v1 import router as api_router

# Import models to ensure they're registered
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
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
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend
        "http://127.0.0.1:5173",
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