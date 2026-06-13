"""Async SQLAlchemy engine and session lifecycle management."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mcd_ua_idw.config import get_settings

AsyncSessionFactory = async_sessionmaker[AsyncSession]

_engine: AsyncEngine | None = None
_session_factory: AsyncSessionFactory | None = None


def build_async_engine(database_url: str) -> AsyncEngine:
    """Build an engine without opening a database connection."""
    return create_async_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    """Build a factory whose sessions retain loaded state after commit."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_engine() -> AsyncEngine:
    """Lazily construct and return the process-wide application engine."""
    global _engine
    if _engine is None:
        _engine = build_async_engine(get_settings().database_url)
    return _engine


def get_session_factory() -> AsyncSessionFactory:
    """Lazily construct the session factory bound to the application engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = build_session_factory(get_engine())
    return _session_factory


async def dispose_engine() -> None:
    """Dispose pooled connections and reset lazy database state."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _session_factory = None
    _engine = None
