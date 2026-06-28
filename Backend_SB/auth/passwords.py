"""
SmartBee — Password hashing with bcrypt
────────────────────────────────────────
bcrypt is the right choice: it's slow by design, salted automatically,
and the work factor can be tuned upward as hardware gets faster.

Never store raw passwords. Never compare passwords with ==.
Always use verify_password().
"""

from passlib.context import CryptContext

# work factor = 12 rounds (~250ms on a modern CPU — comfortable for login, painful for brute force)
_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of `plain`.  Safe to store in the DB."""
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if `plain` matches `hashed`.  Constant-time comparison."""
    return _ctx.verify(plain, hashed)
