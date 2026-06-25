"""
SmartBee — Database engine, session factory, and startup helper
───────────────────────────────────────────────────────────────
Supports both SQLite (dev) and PostgreSQL (production) via DATABASE_URL.

  Dev:  sqlite+aiosqlite:///./smartbee.db
  Prod: postgresql+asyncpg://user:pass@host:5432/smartbee

Usage in a FastAPI route
────────────────────────
  from .database import get_db
  from sqlalchemy.ext.asyncio import AsyncSession

  @router.get("/example")
  async def example(db: AsyncSession = Depends(get_db)):
      result = await db.execute(select(EmailLog))
      return result.scalars().all()

Usage in a sync context (legacy routes, security/keys.py)
─────────────────────────────────────────────────────────
  from .database import get_sync_db
  with get_sync_db() as db:
      db.add(SecureSetting(key="x", value="y"))
      db.commit()
"""

from contextlib import contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models.orm import Base

# ─── Async engine (used by all FastAPI routes) ────────────────────────────────

_async_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # logs every SQL statement in dev
    future=True,
    connect_args=_async_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one AsyncSession per request, auto-closes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── Sync engine (used by security/keys.py until that module is async-ified) ──
#
# SQLite async driver (aiosqlite) can't be used in sync code, so we derive a
# plain sqlite:// or postgresql:// URL from the async one.

def _sync_url(async_url: str) -> str:
    return (
        async_url
        .replace("sqlite+aiosqlite", "sqlite")
        .replace("postgresql+asyncpg", "postgresql+psycopg2")
    )


_sync_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

sync_engine = create_engine(
    _sync_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
    connect_args=_sync_connect_args,
)

# Enable WAL mode on SQLite for better concurrent read performance
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(sync_engine, "connect")
    def _set_wal(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Context manager for sync code — use with `with get_sync_db() as db:`."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── Startup ─────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create all tables that don't yet exist.
    Called once at application startup (see api.py lifespan).

    In production with real migrations (Alembic), swap this body for:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    and run `alembic upgrade head` in your deploy pipeline instead.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
