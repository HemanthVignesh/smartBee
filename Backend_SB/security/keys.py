"""
SmartBee — Secure API Key Management
─────────────────────────────────────
Keys are encrypted with Fernet (AES-128) and stored in the secure_settings
table via SQLAlchemy.  Raw sqlite3 is no longer used anywhere in this module.
"""

import base64
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy import select

from ..config import settings
from ..database import get_sync_db
from ..models.orm import SecureSetting


# ─── Encryption helpers ───────────────────────────────────────────────────────

def _make_fernet() -> Fernet:
    raw    = settings.SECRET_KEY.encode()
    padded = (raw * (32 // len(raw) + 1))[:32]
    return Fernet(base64.urlsafe_b64encode(padded))


def _encrypt(plaintext: str) -> str:
    return _make_fernet().encrypt(plaintext.encode()).decode()


def _decrypt(token: str) -> str:
    return _make_fernet().decrypt(token.encode()).decode()


# ─── Masking ─────────────────────────────────────────────────────────────────

def mask_key(key: str) -> str:
    if not key or len(key) < 5:
        return ""
    return f"••••••••{key[-4:]}"


# ─── DB helpers (now via SQLAlchemy) ─────────────────────────────────────────

def _db_set(name: str, encrypted_value: str) -> None:
    with get_sync_db() as db:
        row = db.get(SecureSetting, name)
        if row:
            row.value = encrypted_value
        else:
            db.add(SecureSetting(key=name, value=encrypted_value))


def _db_get(name: str) -> Optional[str]:
    with get_sync_db() as db:
        row = db.get(SecureSetting, name)
        return row.value if row else None


def _db_delete(name: str) -> None:
    with get_sync_db() as db:
        row = db.get(SecureSetting, name)
        if row:
            db.delete(row)


# ─── Public API ──────────────────────────────────────────────────────────────

def get_active_key(provider: str) -> Optional[str]:
    """
    Return the decrypted API key for `provider` ('gemini' | 'openai').
    Priority: .env > database > None.
    """
    env_key = (
        settings.GEMINI_API_KEY if provider == "gemini" else settings.OPENAI_API_KEY
    )
    if env_key:
        return env_key

    encrypted = _db_get(f"{provider}_api_key")
    if encrypted:
        try:
            return _decrypt(encrypted)
        except Exception:
            return None
    return None


def store_key(provider: str, plaintext_key: str) -> None:
    if not plaintext_key or len(plaintext_key) < 8:
        raise ValueError(f"Key for {provider} is too short to be valid.")
    _db_set(f"{provider}_api_key", _encrypt(plaintext_key))


def delete_key(provider: str) -> None:
    _db_delete(f"{provider}_api_key")


def get_key_status(provider: str) -> dict:
    env_key = (
        settings.GEMINI_API_KEY if provider == "gemini" else settings.OPENAI_API_KEY
    )
    if env_key:
        return {"configured": True, "source": "env", "masked": mask_key(env_key)}

    encrypted = _db_get(f"{provider}_api_key")
    if encrypted:
        try:
            return {
                "configured": True,
                "source": "database",
                "masked": mask_key(_decrypt(encrypted)),
            }
        except Exception:
            pass

    return {"configured": False, "source": "none", "masked": ""}
