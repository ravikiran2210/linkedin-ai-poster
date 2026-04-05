"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _get_async_url(url: str) -> str:
    """Ensure the URL uses the asyncpg driver."""
    # Replace postgresql:// with postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Replace sslmode= with ssl= for asyncpg compatibility
    url = url.replace("sslmode=", "ssl=")
    # Remove channel_binding param (not supported by asyncpg)
    if "channel_binding=" in url:
        import re
        url = re.sub(r"[&?]channel_binding=[^&]*", "", url)
    return url

engine = create_async_engine(
    _get_async_url(settings.database_url),
    echo=False,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Yield an async session – use as FastAPI dependency."""
    async with async_session_factory() as session:
        yield session  # type: ignore[misc]


async def init_db() -> None:
    """Create all tables (dev convenience – use Alembic in prod)."""
    from app.storage.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()
