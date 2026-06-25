from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e1_p02_crear_tablas_tmp_sin_deps"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e1_p02_crear_tablas_tmp_sin_deps.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "tmp_categories",
            "tmp_suppliers",
            "tmp_shippers",
            "tmp_regions",
            "tmp_customers",
        ]
    }
