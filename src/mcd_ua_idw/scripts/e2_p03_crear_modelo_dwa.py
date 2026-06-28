from pathlib import Path

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e2_p03_crear_modelo_dwa"
VERSION = 1


async def run(session):
    sql_path = Path(__file__).parent / "e2_p03_crear_modelo_dwa.sql"
    await run_sql_file(session, sql_path)
    return {
        "tablas_creadas": [
            "dwa_dim_date",
            "dwa_dim_geography",
            "dwa_dim_customer",
            "dwa_dim_product",
            "dwa_dim_employee",
            "dwa_dim_shipper",
            "dwa_fact_order_lines",
            "dwm_customer_history",
            "dwm_product_history",
            "dwa_enr_customer_sales_metrics",
            "dwa_enr_product_sales_metrics",
        ]
    }
