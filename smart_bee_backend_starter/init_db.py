#!/usr/bin/env python3
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