from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e3_p02_crear_tablas_tmp_ingesta2"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e3_p02_crear_tablas_tmp_ingesta2.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "tmp_customers_nov",
            "tmp_products_nov",
            "tmp_orders_nov",
            "tmp_order_details_nov",
        ]
    }
