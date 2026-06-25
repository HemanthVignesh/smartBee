#!/usr/bin/env python3
# Ensure virtualenv site-packages is in sys.path (needed for multiprocessing on macOS)
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir:
    if os.path.exists(os.path.join(current_dir, "venv")):
        venv_dir = os.path.join(current_dir, "venv")
        # Find site-packages directory
        lib_dir = os.path.join(venv_dir, "lib")
        if os.path.exists(lib_dir):
            for py_dir in os.listdir(lib_dir):
                sp = os.path.join(lib_dir, py_dir, "site-packages")
                if os.path.exists(sp) and sp not in sys.path:
                    sys.path.insert(0, sp)
        sp_win = os.path.join(venv_dir, "Lib", "site-packages")
        if os.path.exists(sp_win) and sp_win not in sys.path:
            sys.path.insert(0, sp_win)
        break
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

# Monkeypatch importlib.metadata to prevent slow filesystem scanning/crawling which hangs Pydantic/Uvicorn startup on macOS
import importlib.metadata
importlib.metadata.distributions = lambda *args, **kwargs: []
importlib.metadata.entry_points = lambda *args, **kwargs: {}

"""
Database initialization script for Smart BEE
Creates all database tables defined in the models
"""

from app.db.base import Base
from app.db.session import engine

# Import all models to register them with Base
from app.models.email import Email
from app.models.analysis import EmailAnalysis
from app.models.decision import Decision
from app.models.action import SuggestedAction
from app.models.feedback import UserFeedback
from app.models.user import User
from app.models.audit import AuditLog
from app.models.chat_history import ChatHistory


def init_database():
    """Create all database tables"""
    print("🔧 Initializing Smart BEE database...")
    print(f"📁 Database location: {engine.url}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialized successfully!")
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    init_database()