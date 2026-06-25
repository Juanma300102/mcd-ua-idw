"""Tests for the database connectivity operation."""

from unittest.mock import AsyncMock, Mock

import pytest

from mcd_ua_idw.scripts.util_db_check import check_database


@pytest.mark.asyncio
async def test_check_database_executes_select_one() -> None:
    result = Mock()
    result.scalar_one.return_value = 1
    session = Mock()
    session.execute = AsyncMock(return_value=result)

    await check_database(session)

    statement = session.execute.await_args.args[0]
    assert str(statement) == "SELECT 1"


@pytest.mark.asyncio
async def test_check_database_rejects_unexpected_result() -> None:
    result = Mock()
    result.scalar_one.return_value = 0
    session = Mock()
    session.execute = AsyncMock(return_value=result)

    with pytest.raises(RuntimeError, match="invalid result"):
        await check_database(session)
