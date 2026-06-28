from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e2_p01_crear_tablas_metadata"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e2_p01_crear_tablas_metadata.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "met_entidades",
            "met_atributos",
            "met_procesos",
            "met_indicadores_calidad",
        ]
    }
