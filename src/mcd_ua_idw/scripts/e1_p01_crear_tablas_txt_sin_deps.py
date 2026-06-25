from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e1_p01_crear_tablas_txt_sin_deps"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e1_p01_crear_tablas_txt_sin_deps.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "txt_categories",
            "txt_suppliers",
            "txt_shippers",
            "txt_regions",
            "txt_customers",
        ]
    }
