from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e1_p07_crear_tablas_txt_con_deps"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e1_p07_crear_tablas_txt_con_deps.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "txt_employees",
            "txt_products",
            "txt_territories",
            "txt_employee_territories",
            "txt_orders",
            "txt_order_details",
        ]
    }
