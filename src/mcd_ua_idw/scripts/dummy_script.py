from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

NAME = "Dummy script to test TUI app"  # optional; TUI display label
VERSION = 1  # required; positive integer


async def run(session: AsyncSession) -> dict[str, Any]:
    print("Hello World")
    return {"succeed": True}
