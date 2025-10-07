"""Database engine and session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import Settings, get_settings


class Base(DeclarativeBase):
    """Declarative base class used by all ORM models."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return (and lazily create) the async engine."""
    global _engine, _session_factory
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=False,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    global _session_factory
    if _session_factory is None:
        get_engine(settings=settings)
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def tenant_session(
    tenant_id: str | None,
    settings: Settings | None = None,
) -> AsyncIterator[AsyncSession]:
    """Provide a session scoped to a tenant via PostgreSQL RLS."""
    session_factory = get_session_factory(settings=settings)
    async with session_factory() as session:
        if tenant_id:
            await session.execute(text("SET app.tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        try:
            yield session
        finally:
            if tenant_id:
                await session.execute(text("RESET app.tenant_id"))


async def dispose_engine() -> None:
    """Dispose the engine (used on application shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None

