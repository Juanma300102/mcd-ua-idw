from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e2_p05_cargar_dwa_inicial"
VERSION = 1

_DWA_TABLES = [
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

_REQUIRED_E2_P04_CHECKS = 16

_GEO_SIGNATURE = (
    "COALESCE(NULLIF(TRIM(country), ''), '<unknown>') || '|' || "
    "COALESCE(NULLIF(TRIM(region), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(city), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(postal_code), ''), '<none>')"
)

_CUSTOMER_GEO_SIGNATURE = (
    "COALESCE(NULLIF(TRIM(c.country), ''), '<unknown>') || '|' || "
    "COALESCE(NULLIF(TRIM(c.region), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(c.city), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(c.postal_code), ''), '<none>')"
)

_EMPLOYEE_GEO_SIGNATURE = (
    "COALESCE(NULLIF(TRIM(e.country), ''), '<unknown>') || '|' || "
    "COALESCE(NULLIF(TRIM(e.region), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(e.city), ''), '<none>') || '|' || "
    "'<none>'"
)

_SHIP_GEO_SIGNATURE = (
    "COALESCE(NULLIF(TRIM(o.ship_country), ''), '<unknown>') || '|' || "
    "COALESCE(NULLIF(TRIM(o.ship_region), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(o.ship_city), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(o.ship_postal_code), ''), '<none>')"
)

_STOCK_ALARM_LEVEL = (
    "CASE "
    "WHEN COALESCE(p.units_in_stock, 0) <= 0 THEN 2 "
    "WHEN p.units_in_stock <= COALESCE(p.reorder_level, 0) THEN 1 "
    "ELSE 0 END"
)

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado, observaciones) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, :estado, :observaciones)"
)

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)

_INSERT_DATE_DIM = text(
    "WITH source_dates AS ("
    "  SELECT order_date AS fecha FROM tmp_orders WHERE order_date IS NOT NULL "
    "  UNION "
    "  SELECT required_date AS fecha FROM tmp_orders WHERE required_date IS NOT NULL "
    "  UNION "
    "  SELECT shipped_date AS fecha FROM tmp_orders WHERE shipped_date IS NOT NULL"
    "), normalized AS ("
    "  SELECT DISTINCT CAST(fecha AS DATE) AS full_date FROM source_dates"
    ") "
    "INSERT INTO dwa_dim_date "
    "(date_key, full_date, year_number, quarter_number, month_number, day_number) "
    "SELECT "
    "  CAST(EXTRACT(YEAR FROM full_date) AS INTEGER) * 10000 "
    "    + CAST(EXTRACT(MONTH FROM full_date) AS INTEGER) * 100 "
    "    + CAST(EXTRACT(DAY FROM full_date) AS INTEGER) AS date_key, "
    "  full_date, "
    "  CAST(EXTRACT(YEAR FROM full_date) AS INTEGER), "
    "  CAST(EXTRACT(QUARTER FROM full_date) AS INTEGER), "
    "  CAST(EXTRACT(MONTH FROM full_date) AS INTEGER), "
    "  CAST(EXTRACT(DAY FROM full_date) AS INTEGER) "
    "FROM normalized"
)

_INSERT_GEOGRAPHY_DIM = text(
    "WITH source_geo AS ("
    "  SELECT country, region, city, postal_code FROM tmp_customers "
    "  UNION "
    "  SELECT country, region, city, CAST(NULL AS TEXT) AS postal_code FROM tmp_employees "
    "  UNION "
    "  SELECT ship_country AS country, ship_region AS region, ship_city AS city, "
    "         ship_postal_code AS postal_code "
    "  FROM tmp_orders"
    "), signed AS ("
    f"  SELECT {_GEO_SIGNATURE} AS geography_signature, "
    "         country, region, city, postal_code "
    "  FROM source_geo"
    "), normalized AS ("
    "  SELECT geography_signature, MIN(country) AS country, MIN(region) AS region, "
    "         MIN(city) AS city, MIN(postal_code) AS postal_code "
    "  FROM signed "
    "  GROUP BY geography_signature"
    ") "
    "INSERT INTO dwa_dim_geography "
    "(geography_signature, country, region, city, postal_code) "
    "SELECT geography_signature, country, region, city, postal_code "
    "FROM normalized"
)

_INSERT_CUSTOMER_DIM = text(
    "INSERT INTO dwa_dim_customer "
    "(customer_id, customer_geography_key, company_name, contact_name, contact_title, "
    "city, region, postal_code, country, phone, fax) "
    "SELECT c.customer_id, g.geography_key, c.company_name, c.contact_name, "
    "c.contact_title, c.city, c.region, c.postal_code, c.country, c.phone, c.fax "
    "FROM tmp_customers c "
    f"JOIN dwa_dim_geography g ON g.geography_signature = {_CUSTOMER_GEO_SIGNATURE}"
)

_INSERT_PRODUCT_DIM = text(
    "INSERT INTO dwa_dim_product "
    "(product_id, product_name, category_id, category_name, supplier_id, "
    "supplier_name, quantity_per_unit, unit_price, units_in_stock, units_on_order, "
    "reorder_level, discontinued, stock_alarm_level) "
    "SELECT p.product_id, p.product_name, p.category_id, c.category_name, "
    "p.supplier_id, s.company_name, p.quantity_per_unit, p.unit_price, "
    "p.units_in_stock, p.units_on_order, p.reorder_level, p.discontinued, "
    f"{_STOCK_ALARM_LEVEL} "
    "FROM tmp_products p "
    "LEFT JOIN tmp_categories c ON p.category_id = c.category_id "
    "LEFT JOIN tmp_suppliers s ON p.supplier_id = s.supplier_id"
)

_INSERT_EMPLOYEE_DIM = text(
    "INSERT INTO dwa_dim_employee "
    "(employee_id, employee_geography_key, employee_name, title, city, region, "
    "country, reports_to) "
    "SELECT e.employee_id, g.geography_key, "
    "e.first_name || ' ' || e.last_name AS employee_name, e.title, "
    "e.city, e.region, e.country, e.reports_to "
    "FROM tmp_employees e "
    f"JOIN dwa_dim_geography g ON g.geography_signature = {_EMPLOYEE_GEO_SIGNATURE}"
)

_INSERT_SHIPPER_DIM = text(
    "INSERT INTO dwa_dim_shipper (shipper_id, company_name, phone) "
    "SELECT shipper_id, company_name, phone "
    "FROM tmp_shippers"
)

_INSERT_FACT_ORDER_LINES = text(
    "INSERT INTO dwa_fact_order_lines "
    "(order_id, product_id, customer_key, product_key, employee_key, shipper_key, "
    "ship_geography_key, order_date_key, required_date_key, shipped_date_key, "
    "unit_price, quantity, discount, gross_amount, discount_amount, net_amount, "
    "order_freight_amount) "
    "SELECT "
    "  o.order_id, "
    "  od.product_id, "
    "  c.customer_key, "
    "  p.product_key, "
    "  e.employee_key, "
    "  s.shipper_key, "
    "  ship_geo.geography_key, "
    "  order_date.date_key, "
    "  required_date.date_key, "
    "  shipped_date.date_key, "
    "  od.unit_price, "
    "  od.quantity, "
    "  COALESCE(od.discount, 0), "
    "  od.unit_price * od.quantity, "
    "  od.unit_price * od.quantity * COALESCE(od.discount, 0), "
    "  od.unit_price * od.quantity * (1 - COALESCE(od.discount, 0)), "
    "  o.freight "
    "FROM tmp_order_details od "
    "JOIN tmp_orders o ON od.order_id = o.order_id "
    "JOIN dwa_dim_customer c ON o.customer_id = c.customer_id "
    "JOIN dwa_dim_product p ON od.product_id = p.product_id "
    "JOIN dwa_dim_employee e ON o.employee_id = e.employee_id "
    "JOIN dwa_dim_shipper s ON o.ship_via = s.shipper_id "
    f"JOIN dwa_dim_geography ship_geo ON ship_geo.geography_signature = {_SHIP_GEO_SIGNATURE} "
    "JOIN dwa_dim_date order_date "
    "  ON CAST(o.order_date AS DATE) = order_date.full_date "
    "JOIN dwa_dim_date required_date "
    "  ON CAST(o.required_date AS DATE) = required_date.full_date "
    "LEFT JOIN dwa_dim_date shipped_date "
    "  ON CAST(o.shipped_date AS DATE) = shipped_date.full_date"
)

_INSERT_CUSTOMER_HISTORY = text(
    "INSERT INTO dwm_customer_history "
    "(customer_id, company_name, contact_name, contact_title, city, region, "
    "postal_code, country, phone, fax, attribute_signature, vigente_desde, "
    "vigente_hasta, es_vigente) "
    "SELECT customer_id, company_name, contact_name, contact_title, city, region, "
    "postal_code, country, phone, fax, "
    "COALESCE(company_name, '') || '|' || COALESCE(contact_name, '') || '|' || "
    "COALESCE(contact_title, '') || '|' || COALESCE(city, '') || '|' || "
    "COALESCE(region, '') || '|' || COALESCE(postal_code, '') || '|' || "
    "COALESCE(country, '') || '|' || COALESCE(phone, '') || '|' || COALESCE(fax, ''), "
    "CURRENT_TIMESTAMP, NULL, 1 "
    "FROM tmp_customers"
)

_INSERT_PRODUCT_HISTORY = text(
    "INSERT INTO dwm_product_history "
    "(product_id, product_name, category_id, category_name, supplier_id, "
    "supplier_name, quantity_per_unit, unit_price, units_in_stock, units_on_order, "
    "reorder_level, discontinued, stock_alarm_level, attribute_signature, "
    "vigente_desde, vigente_hasta, es_vigente) "
    "SELECT p.product_id, p.product_name, p.category_id, c.category_name, "
    "p.supplier_id, s.company_name, p.quantity_per_unit, p.unit_price, "
    "p.units_in_stock, p.units_on_order, p.reorder_level, p.discontinued, "
    f"{_STOCK_ALARM_LEVEL}, "
    "COALESCE(p.product_name, '') || '|' || COALESCE(CAST(p.category_id AS TEXT), '') "
    "|| '|' || COALESCE(c.category_name, '') || '|' || "
    "COALESCE(CAST(p.supplier_id AS TEXT), '') || '|' || COALESCE(s.company_name, '') "
    "|| '|' || COALESCE(p.quantity_per_unit, '') || '|' || "
    "COALESCE(CAST(p.unit_price AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.units_in_stock AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.units_on_order AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.reorder_level AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.discontinued AS TEXT), ''), "
    "CURRENT_TIMESTAMP, NULL, 1 "
    "FROM tmp_products p "
    "LEFT JOIN tmp_categories c ON p.category_id = c.category_id "
    "LEFT JOIN tmp_suppliers s ON p.supplier_id = s.supplier_id"
)

_INSERT_CUSTOMER_ENRICHMENT = text(
    # Sales-only by design: this enrichment keeps customers that appear in the fact.
    # Reference: DOCS/TP anteriores de ejemplo/ejemplo/TP DWA informe ejemplo.pdf,
    # section 4.1 supports DWA-derived BI metrics; the sales-only grain is this
    # project's decision, documented in DOCS/decisiones_de_diseno.md.
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
    "first_order_date, last_order_date) "
    "SELECT c.customer_key, c.customer_id, om.order_count, lm.order_line_count, "
    "lm.total_quantity, lm.gross_amount, lm.discount_amount, lm.net_amount, "
    "om.avg_order_net_amount, om.first_order_date, om.last_order_date "
    "FROM dwa_dim_customer c "
    "JOIN line_metrics lm ON c.customer_key = lm.customer_key "
    "JOIN order_metrics om ON c.customer_key = om.customer_key"
)

_INSERT_PRODUCT_ENRICHMENT = text(
    "INSERT INTO dwa_enr_product_sales_metrics "
    "(product_key, product_id, order_count, order_line_count, total_quantity, "
    "gross_amount, discount_amount, net_amount, avg_line_net_amount, "
    "first_order_date, last_order_date) "
    "SELECT p.product_key, p.product_id, COUNT(DISTINCT f.order_id), COUNT(*), "
    "SUM(f.quantity), SUM(f.gross_amount), SUM(f.discount_amount), SUM(f.net_amount), "
    "AVG(f.net_amount), MIN(d.full_date), MAX(d.full_date) "
    "FROM dwa_fact_order_lines f "
    "JOIN dwa_dim_product p ON f.product_key = p.product_key "
    "JOIN dwa_dim_date d ON f.order_date_key = d.date_key "
    "GROUP BY p.product_key, p.product_id"
)

_LOAD_STEPS = [
    ("dwa_dim_date", _INSERT_DATE_DIM),
    ("dwa_dim_geography", _INSERT_GEOGRAPHY_DIM),
    ("dwa_dim_customer", _INSERT_CUSTOMER_DIM),
    ("dwa_dim_product", _INSERT_PRODUCT_DIM),
    ("dwa_dim_employee", _INSERT_EMPLOYEE_DIM),
    ("dwa_dim_shipper", _INSERT_SHIPPER_DIM),
    ("dwa_fact_order_lines", _INSERT_FACT_ORDER_LINES),
    ("dwm_customer_history", _INSERT_CUSTOMER_HISTORY),
    ("dwm_product_history", _INSERT_PRODUCT_HISTORY),
    ("dwa_enr_customer_sales_metrics", _INSERT_CUSTOMER_ENRICHMENT),
    ("dwa_enr_product_sales_metrics", _INSERT_PRODUCT_ENRICHMENT),
]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _check_e2_p04_latest_validations(session) -> None:
    row = (
        await session.execute(
            text(
                "WITH ultimas AS ("
                "  SELECT tabla, columna, tipo_chequeo, resultado, detalle, "
                "         ROW_NUMBER() OVER ("
                "           PARTITION BY tabla, columna, tipo_chequeo "
                "           ORDER BY fecha DESC, id DESC"
                "         ) AS rn "
                "  FROM dqm_validaciones "
                "  WHERE nombre_script = 'e2_p04_validar_carga_dwa'"
                ") "
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE resultado = 'ERROR') AS errores "
                "FROM ultimas "
                "WHERE rn = 1"
            )
        )
    ).one()

    if row.total < _REQUIRED_E2_P04_CHECKS:
        raise RuntimeError(
            "e2_p04_validar_carga_dwa debe ejecutarse correctamente antes de "
            "cargar DWA. "
            f"Validaciones actuales: {row.total}; esperadas al menos "
            f"{_REQUIRED_E2_P04_CHECKS}."
        )
    if row.errores > 0:
        raise RuntimeError(
            "Hay validaciones ERROR vigentes de e2_p04_validar_carga_dwa. "
            "Corregir antes de cargar DWA."
        )


async def _check_idempotencia(session) -> None:
    for table in _DWA_TABLES:
        count = (
            await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        ).scalar_one()
        if count > 0:
            raise RuntimeError(
                f"{table} ya tiene {count} fila(s). "
                "Truncar o recrear las tablas DWA manualmente antes de recargar."
            )


async def _count_rows(session, table: str) -> int:
    return (await session.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one()


async def _record_event(
    session,
    *,
    table: str,
    started_at: datetime,
    finished_at: datetime,
    rows: int,
) -> None:
    await session.execute(
        _INSERT_EVENTO,
        {
            "tabla": table,
            "tipo_evento": "CARGA_DWA",
            "nombre_script": NAME,
            "fecha_inicio": started_at,
            "fecha_fin": finished_at,
            "registros_procesados": rows,
            "estado": "OK",
            "observaciones": "Carga inicial DWA desde TMP validada.",
        },
    )


async def _record_fact_count_validation(session) -> dict[str, int | str]:
    source_count = await _count_rows(session, "tmp_order_details")
    fact_count = await _count_rows(session, "dwa_fact_order_lines")
    diff = abs(fact_count - source_count)
    indicador = diff / source_count if source_count > 0 else 0.0
    resultado = "OK" if diff == 0 else "ERROR"
    detalle = (
        "Cantidad de filas del hecho coincide con tmp_order_details."
        if diff == 0
        else (
            "Cantidad de filas del hecho no coincide: "
            f"tmp_order_details={source_count}, dwa_fact_order_lines={fact_count}."
        )
    )

    await session.execute(
        _INSERT_VAL,
        {
            "tabla": "dwa_fact_order_lines",
            "columna": None,
            "tipo_chequeo": "DWA_CONTEO_FACT",
            "nombre_script": NAME,
            "total": source_count,
            "afectados": diff,
            "indicador": indicador,
            "umbral": 0.0,
            "resultado": resultado,
            "detalle": detalle,
        },
    )
    return {
        "resultado": resultado,
        "filas_fuente": source_count,
        "filas_hecho": fact_count,
        "diferencia": diff,
    }


async def run(session):
    await _check_e2_p04_latest_validations(session)
    await _check_idempotencia(session)

    filas_cargadas = {}
    for table, statement in _LOAD_STEPS:
        started_at = _now()
        await session.execute(statement)
        finished_at = _now()
        rows = await _count_rows(session, table)
        filas_cargadas[table] = rows
        await _record_event(
            session,
            table=table,
            started_at=started_at,
            finished_at=finished_at,
            rows=rows,
        )

    conteo_fact = await _record_fact_count_validation(session)

    return {"filas_cargadas": filas_cargadas, "conteo_fact": conteo_fact}
