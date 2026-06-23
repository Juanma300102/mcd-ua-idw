from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def run_sql_file(session: AsyncSession, path: Path) -> None:
    """Ejecuta el contenido completo de un archivo .sql en una sola sentencia
    multi-statement. No hace commit/rollback - lo maneja runner.py."""
    sql = Path(path).read_text(encoding="utf-8")
    await session.execute(text(sql))
