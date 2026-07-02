from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e4_p01_crear_tablas_publicacion"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e4_p01_crear_tablas_publicacion.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "dp01_ventas_geo_score",
            "dp02_dqm_validaciones_resumen",
            "dp02_dqm_eventos_resumen",
            "dp02_dqm_perfilado_resumen",
        ]
    }
