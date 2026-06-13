"""Offline tests for async engine and session construction."""

import pytest

from mcd_ua_idw.db.session import build_async_engine, build_session_factory


DATABASE_URL = "postgresql+psycopg://app:app@localhost:5432/app"


@pytest.mark.asyncio
async def test_build_session_factory_creates_isolated_sessions() -> None:
    engine = build_async_engine(DATABASE_URL)
    factory = build_session_factory(engine)
    first = factory()
    second = factory()

    try:
        assert first is not second
        assert first.bind is engine
        assert second.bind is engine
        assert first.sync_session.expire_on_commit is False
    finally:
        await first.close()
        await second.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_build_async_engine_enables_connection_health_checks() -> None:
    engine = build_async_engine(DATABASE_URL)

    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.pool._pre_ping is True
    finally:
        await engine.dispose()
