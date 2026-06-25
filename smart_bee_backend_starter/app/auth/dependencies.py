"""
auth/dependencies.py

Drop-in FastAPI dependency that validates the Bearer JWT on every request
and returns the authenticated User ORM object.

Usage in any route:
    from app.auth.dependencies import get_current_user
    from app.models.user import User

    @router.get("/something")
    def my_route(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.auth.jwt import decode_access_token
from app.models.user import User

# HTTPBearer extracts the "Authorization: Bearer <token>" header automatically
_bearer_scheme = HTTPBearer(auto_error=False)


# ── DB dependency (mirrors every router's get_db) ────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Core dependency ──────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT and return the matching User row.

    Raises 401 for missing/invalid/expired tokens.
    Raises 403 if the account is deactivated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — please sign in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return user


# ── Optional variant (returns None when unauthenticated) ─────────────────────

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising 401."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    user_id: str = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()
