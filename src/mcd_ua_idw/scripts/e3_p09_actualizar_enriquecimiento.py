from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e3_p09_actualizar_enriquecimiento"
VERSION = 1

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado, observaciones) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, :estado, :observaciones)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def run(session):
    resumen = {}

    # Recalcular metricas de clientes — DELETE + INSERT completo desde el hecho
    t0 = _now()
    await session.execute(text("DELETE FROM dwa_enr_customer_sales_metrics"))
    result = await session.execute(text(
        "WITH line_metrics AS ("
        "  SELECT customer_key, "
        "         COUNT(*) AS order_line_count, "
        "         SUM(quantity) AS total_quantity, "
        "         SUM(gross_amount) AS gross_amount, "
        "         SUM(discount_amount) AS discount_amount, "
        "         SUM(net_amount) AS net_amount "
        "  FROM dwa_fact_order_lines "
        "  GROUP BY customer_key"
        "), order_metrics AS ("
        "  SELECT orders.customer_key, "
        "         COUNT(*) AS order_count, "
        "         AVG(orders.order_net_amount) AS avg_order_net_amount, "
        "         MIN(d.full_date) AS first_order_date, "
        "         MAX(d.full_date) AS last_order_date "
        "  FROM ("
        "    SELECT customer_key, order_id, MIN(order_date_key) AS order_date_key, "
        "           SUM(net_amount) AS order_net_amount "
        "    FROM dwa_fact_order_lines "
        "    GROUP BY customer_key, order_id"
        "  ) orders "
        "  JOIN dwa_dim_date d ON orders.order_date_key = d.date_key "
        "  GROUP BY orders.customer_key"
        ") "
        "INSERT INTO dwa_enr_customer_sales_metrics "
        "(customer_key, customer_id, order_count, order_line_count, total_quantity, "
        "gross_amount, discount_amount, net_amount, avg_order_net_amount, "
        "first_order_date, last_order_date, fecha_calculo) "
        "SELECT c.customer_key, c.customer_id, om.order_count, lm.order_line_count, "
        "lm.total_quantity, lm.gross_amount, lm.discount_amount, lm.net_amount, "
        "om.avg_order_net_amount, om.first_order_date, om.last_order_date, "
        "CURRENT_TIMESTAMP "
        "FROM dwa_dim_customer c "
        "JOIN line_metrics lm ON c.customer_key = lm.customer_key "
        "JOIN order_metrics om ON c.customer_key = om.customer_key"
    ))
    n_cust = result.rowcount
    resumen["dwa_enr_customer_sales_metrics"] = n_cust
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_enr_customer_sales_metrics",
        "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME,
        "fecha_inicio": t0,
        "fecha_fin": _now(),
        "registros_procesados": n_cust,
        "estado": "OK",
        "observaciones": "Recalculo completo post-Ingesta2",
    })

    # Recalcular metricas de productos
    t0 = _now()
    await session.execute(text("DELETE FROM dwa_enr_product_sales_metrics"))
    result = await session.execute(text(
        "INSERT INTO dwa_enr_product_sales_metrics "
        "(product_key, product_id, order_count, order_line_count, total_quantity, "
        "gross_amount, discount_amount, net_amount, avg_line_net_amount, "
        "first_order_date, last_order_date, fecha_calculo) "
        "SELECT p.product_key, p.product_id, COUNT(DISTINCT f.order_id), COUNT(*), "
        "SUM(f.quantity), SUM(f.gross_amount), SUM(f.discount_amount), SUM(f.net_amount), "
        "AVG(f.net_amount), MIN(d.full_date), MAX(d.full_date), CURRENT_TIMESTAMP "
        "FROM dwa_fact_order_lines f "
        "JOIN dwa_dim_product p ON f.product_key = p.product_key "
        "JOIN dwa_dim_date d ON f.order_date_key = d.date_key "
        "GROUP BY p.product_key, p.product_id"
    ))
    n_prod = result.rowcount
    resumen["dwa_enr_product_sales_metrics"] = n_prod
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_enr_product_sales_metrics",
        "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME,
        "fecha_inicio": t0,
        "fecha_fin": _now(),
        "registros_procesados": n_prod,
        "estado": "OK",
        "observaciones": "Recalculo completo post-Ingesta2",
    })

    return resumen
