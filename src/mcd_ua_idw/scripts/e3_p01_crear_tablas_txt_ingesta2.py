from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e3_p01_crear_tablas_txt_ingesta2"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e3_p01_crear_tablas_txt_ingesta2.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "txt_customers_nov",
            "txt_products_nov",
            "txt_orders_nov",
            "txt_order_details_nov",
        ]
    }
