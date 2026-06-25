from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e0_p01_crear_tablas_dqm"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e0_p01_crear_tablas_dqm.sql"
    await run_sql_file(session, sql_path)
    return {"tablas_creadas": ["dqm_eventos", "dqm_validaciones", "dqm_perfilado"]}
