"""Verify database connectivity through the standard session boundary."""

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mcd_ua_idw.db import dispose_engine, get_session_factory

NAME = "Database connectivity check"
VERSION = 1


async def check_database(session: AsyncSession) -> None:
    """Execute a minimal query using a caller-owned session."""
    result = await session.execute(text("SELECT 1"))
    if result.scalar_one() != 1:
        raise RuntimeError("Database connectivity check returned an invalid result")


async def run(session: AsyncSession) -> dict[str, Any]:
    """Run the check using a caller-owned session."""
    await check_database(session)
    return {"database": "connected"}


async def run_standalone() -> None:
    """Run the check in one atomic, short-lived transaction."""
    try:
        async with get_session_factory().begin() as session:
            await run(session)
        print("Database connection successful.")
    finally:
        await dispose_engine()


def main() -> None:
    """Synchronous console-script boundary."""
    asyncio.run(run_standalone())


if __name__ == "__main__":
    main()
