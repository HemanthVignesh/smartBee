"""
SmartBee — FastAPI auth dependencies
──────────────────────────────────────
Usage in any route:

    from ..auth.dependencies import get_current_user
    from ..models.orm import User

    @router.get("/my-data")
    async def my_data(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        ...

get_current_user
    Reads the Authorization: Bearer <token> header.
    Validates the JWT.  Loads the User row.  Returns it.
    Raises HTTP 401 on any failure — never leaks whether the user exists.

get_current_active_user
    Same as above but also checks is_active=True.
    Use this on all normal routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.tokens import decode_token
from ..database import get_db
from ..models.orm import User

_bearer = HTTPBearer(auto_error=False)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

_403 = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Account is disabled",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract, verify JWT, load and return User. Raises 401 on any failure."""
    if credentials is None:
        raise _401

    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except JWTError:
        raise _401

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise _401

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Like get_current_user but also rejects disabled accounts."""
    if not current_user.is_active:
        raise _403
    return current_user
