import sqlite3
from .config import DATABASE_PATH


def get_connection():
    """
    Returns a SQLite connection safe for FastAPI usage.
    """
    conn = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False  # ✅ Important for FastAPI
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes required database tables.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            intent TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()
