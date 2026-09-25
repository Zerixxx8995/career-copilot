"""
Database engine + session factory.
Uses async SQLAlchemy with asyncpg for Neon/PostgreSQL.
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# Convert postgresql:// → postgresql+asyncpg:// if needed
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg doesn't understand sslmode/channel_binding query params — strip them
# and pass ssl=True via connect_args instead
import re as _re
_has_ssl = bool(_re.search(r"sslmode=require", _db_url, _re.IGNORECASE))
_db_url = _re.sub(r"[?&]sslmode=[^&]*", "", _db_url)
_db_url = _re.sub(r"[?&]channel_binding=[^&]*", "", _db_url)
_db_url = _db_url.rstrip("?&")

_connect_args = {"ssl": "require"} if _has_ssl else {}

engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def init_db() -> None:
    """Create all tables on startup (dev convenience; use Alembic in production)."""
    from app.models import feedback_models, job_models, profile_models, trace_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")


async def get_db() -> AsyncSession:  # type: ignore[return]
    """Dependency that provides an async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
