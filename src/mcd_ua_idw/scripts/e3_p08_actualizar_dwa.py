from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e3_p08_actualizar_dwa"
VERSION = 1

_TABLAS_NOV = [
    "txt_customers_nov",
    "txt_products_nov",
    "txt_orders_nov",
    "txt_order_details_nov",
]

_CUSTOMER_SIGNATURE = (
    "COALESCE(company_name, '') || '|' || COALESCE(contact_name, '') || '|' || "
    "COALESCE(contact_title, '') || '|' || COALESCE(city, '') || '|' || "
    "COALESCE(region, '') || '|' || COALESCE(postal_code, '') || '|' || "
    "COALESCE(country, '') || '|' || COALESCE(phone, '') || '|' || COALESCE(fax, '')"
)

_PRODUCT_SIGNATURE = (
    "COALESCE(p.product_name, '') || '|' || COALESCE(CAST(p.category_id AS TEXT), '') "
    "|| '|' || COALESCE(CAST(p.supplier_id AS TEXT), '') || '|' || "
    "COALESCE(p.quantity_per_unit, '') || '|' || "
    "COALESCE(CAST(p.unit_price AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.units_in_stock AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.units_on_order AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.reorder_level AS TEXT), '') || '|' || "
    "COALESCE(CAST(p.discontinued AS TEXT), '')"
)

_STOCK_ALARM_LEVEL = (
    "CASE "
    "WHEN COALESCE(p.units_in_stock, 0) <= 0 THEN 2 "
    "WHEN p.units_in_stock <= COALESCE(p.reorder_level, 0) THEN 1 "
    "ELSE 0 END"
)

_GEO_SIG_EXPR = (
    "COALESCE(NULLIF(TRIM(ship_country), ''), '<unknown>') || '|' || "
    "COALESCE(NULLIF(TRIM(ship_region), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(ship_city), ''), '<none>') || '|' || "
    "COALESCE(NULLIF(TRIM(ship_postal_code), ''), '<none>')"
)

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado, observaciones) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, :estado, :observaciones)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _check_integridad_nov(session) -> None:
    rows = (await session.execute(text(
        "SELECT tabla, columna, tipo_chequeo, detalle "
        "FROM dqm_validaciones "
        "WHERE resultado = 'ERROR' AND tabla = ANY(:tablas) "
        "AND nombre_script = 'e3_p07_validar_integridad_ingesta2'"
    ), {"tablas": _TABLAS_NOV})).fetchall()

    if rows:
        detalle = "; ".join(
            f"{r.tabla}.{r.columna} [{r.tipo_chequeo}]: {r.detalle}" for r in rows
        )
        raise RuntimeError(
            f"e3_p07 registra {len(rows)} error(es) de integridad. "
            f"Corregir antes de actualizar DWA. Detalle: {detalle}"
        )


async def _insertar_fechas_nuevas(session) -> int:
    result = await session.execute(text(
        "INSERT INTO dwa_dim_date "
        "(date_key, full_date, year_number, quarter_number, month_number, day_number) "
        "WITH source_dates AS ("
        "  SELECT order_date AS f FROM tmp_orders_nov WHERE order_date IS NOT NULL "
        "  UNION "
        "  SELECT required_date FROM tmp_orders_nov WHERE required_date IS NOT NULL "
        "  UNION "
        "  SELECT shipped_date FROM tmp_orders_nov WHERE shipped_date IS NOT NULL"
        "), normalized AS ("
        "  SELECT DISTINCT CAST(f AS DATE) AS full_date FROM source_dates"
        ") "
        "SELECT "
        "  CAST(EXTRACT(YEAR FROM full_date) AS INTEGER) * 10000 "
        "    + CAST(EXTRACT(MONTH FROM full_date) AS INTEGER) * 100 "
        "    + CAST(EXTRACT(DAY FROM full_date) AS INTEGER), "
        "  full_date, "
        "  CAST(EXTRACT(YEAR FROM full_date) AS INTEGER), "
        "  CAST(EXTRACT(QUARTER FROM full_date) AS INTEGER), "
        "  CAST(EXTRACT(MONTH FROM full_date) AS INTEGER), "
        "  CAST(EXTRACT(DAY FROM full_date) AS INTEGER) "
        "FROM normalized "
        "WHERE full_date NOT IN (SELECT full_date FROM dwa_dim_date) "
        "ON CONFLICT DO NOTHING"
    ))
    return result.rowcount


async def _insertar_geografias_nuevas(session) -> int:
    result = await session.execute(text(
        f"INSERT INTO dwa_dim_geography (geography_signature, country, region, city, postal_code) "
        f"SELECT DISTINCT "
        f"  {_GEO_SIG_EXPR} AS geography_signature, "
        f"  ship_country, ship_region, ship_city, ship_postal_code "
        f"FROM tmp_orders_nov "
        f"WHERE {_GEO_SIG_EXPR} NOT IN (SELECT geography_signature FROM dwa_dim_geography) "
        f"ON CONFLICT DO NOTHING"
    ))
    return result.rowcount


async def _aplicar_scd2_customers(session) -> dict:
    customers_nov = (await session.execute(text(
        f"SELECT customer_id, company_name, contact_name, contact_title, "
        f"address, city, region, postal_code, country, phone, fax, "
        f"{_CUSTOMER_SIGNATURE} AS new_sig "
        f"FROM tmp_customers_nov"
    ))).fetchall()

    modificados = []
    for row in customers_nov:
        current = (await session.execute(text(
            "SELECT attribute_signature FROM dwm_customer_history "
            "WHERE customer_id = :cid AND es_vigente = 1"
        ), {"cid": row.customer_id})).fetchone()

        if current is None or current.attribute_signature != row.new_sig:
            if current is not None:
                # Cerrar version anterior
                await session.execute(text(
                    "UPDATE dwm_customer_history "
                    "SET vigente_hasta = CURRENT_TIMESTAMP, es_vigente = 0 "
                    "WHERE customer_id = :cid AND es_vigente = 1"
                ), {"cid": row.customer_id})

            # Insertar nueva version en historia
            await session.execute(text(
                "INSERT INTO dwm_customer_history "
                "(customer_id, company_name, contact_name, contact_title, city, region, "
                "postal_code, country, phone, fax, attribute_signature, vigente_desde, "
                "vigente_hasta, es_vigente) "
                "VALUES (:cid, :company, :contact, :title, :city, :region, "
                ":postal, :country, :phone, :fax, :sig, CURRENT_TIMESTAMP, NULL, 1)"
            ), {
                "cid": row.customer_id,
                "company": row.company_name,
                "contact": row.contact_name,
                "title": row.contact_title,
                "city": row.city,
                "region": row.region,
                "postal": row.postal_code,
                "country": row.country,
                "phone": row.phone,
                "fax": row.fax,
                "sig": row.new_sig,
            })

            # Actualizar dimension actual
            await session.execute(text(
                "UPDATE dwa_dim_customer SET "
                "company_name = :company, contact_name = :contact, "
                "contact_title = :title, city = :city, region = :region, "
                "postal_code = :postal, country = :country, phone = :phone, fax = :fax "
                "WHERE customer_id = :cid"
            ), {
                "cid": row.customer_id,
                "company": row.company_name,
                "contact": row.contact_name,
                "title": row.contact_title,
                "city": row.city,
                "region": row.region,
                "postal": row.postal_code,
                "country": row.country,
                "phone": row.phone,
                "fax": row.fax,
            })
            modificados.append(row.customer_id)

    return {"modificados": modificados, "total": len(customers_nov)}


async def _aplicar_scd2_products(session) -> dict:
    products_nov = (await session.execute(text(
        f"SELECT p.product_id, p.product_name, p.supplier_id, "
        f"p.category_id, p.quantity_per_unit, p.unit_price, "
        f"p.units_in_stock, p.units_on_order, p.reorder_level, p.discontinued, "
        f"COALESCE(c.category_name, '') AS category_name, "
        f"COALESCE(s.company_name, '') AS supplier_name, "
        f"{_PRODUCT_SIGNATURE} AS new_sig, "
        f"{_STOCK_ALARM_LEVEL} AS new_stock_alarm "
        f"FROM tmp_products_nov p "
        f"LEFT JOIN tmp_categories c ON p.category_id = c.category_id "
        f"LEFT JOIN tmp_suppliers s ON p.supplier_id = s.supplier_id"
    ))).fetchall()

    modificados = []
    for row in products_nov:
        current = (await session.execute(text(
            "SELECT attribute_signature FROM dwm_product_history "
            "WHERE product_id = :pid AND es_vigente = 1"
        ), {"pid": row.product_id})).fetchone()

        if current is None or current.attribute_signature != row.new_sig:
            if current is not None:
                await session.execute(text(
                    "UPDATE dwm_product_history "
                    "SET vigente_hasta = CURRENT_TIMESTAMP, es_vigente = 0 "
                    "WHERE product_id = :pid AND es_vigente = 1"
                ), {"pid": row.product_id})

            await session.execute(text(
                "INSERT INTO dwm_product_history "
                "(product_id, product_name, category_id, category_name, supplier_id, "
                "supplier_name, quantity_per_unit, unit_price, units_in_stock, units_on_order, "
                "reorder_level, discontinued, stock_alarm_level, attribute_signature, "
                "vigente_desde, vigente_hasta, es_vigente) "
                "VALUES (:pid, :pname, :cat_id, :cat_name, :sup_id, :sup_name, "
                ":qpu, :price, :stock, :on_order, :reorder, :disc, :alarm, :sig, "
                "CURRENT_TIMESTAMP, NULL, 1)"
            ), {
                "pid": row.product_id,
                "pname": row.product_name,
                "cat_id": row.category_id,
                "cat_name": row.category_name,
                "sup_id": row.supplier_id,
                "sup_name": row.supplier_name,
                "qpu": row.quantity_per_unit,
                "price": row.unit_price,
                "stock": row.units_in_stock,
                "on_order": row.units_on_order,
                "reorder": row.reorder_level,
                "disc": row.discontinued,
                "alarm": row.new_stock_alarm,
                "sig": row.new_sig,
            })

            await session.execute(text(
                "UPDATE dwa_dim_product SET "
                "product_name = :pname, unit_price = :price, "
                "units_in_stock = :stock, units_on_order = :on_order, "
                "reorder_level = :reorder, discontinued = :disc, "
                "stock_alarm_level = :alarm "
                "WHERE product_id = :pid"
            ), {
                "pid": row.product_id,
                "pname": row.product_name,
                "price": row.unit_price,
                "stock": row.units_in_stock,
                "on_order": row.units_on_order,
                "reorder": row.reorder_level,
                "disc": row.discontinued,
                "alarm": row.new_stock_alarm,
            })
            modificados.append(row.product_id)

    return {"modificados": modificados, "total": len(products_nov)}


async def _insertar_nuevas_ordenes(session) -> int:
    result = await session.execute(text(
        f"INSERT INTO dwa_fact_order_lines "
        f"(order_id, product_id, customer_key, product_key, employee_key, shipper_key, "
        f"ship_geography_key, order_date_key, required_date_key, shipped_date_key, "
        f"unit_price, quantity, discount, gross_amount, discount_amount, net_amount, "
        f"order_freight_amount) "
        f"SELECT "
        f"  od.order_id, od.product_id, "
        f"  c.customer_key, p.product_key, e.employee_key, sh.shipper_key, "
        f"  g.geography_key, "
        f"  od_key.date_key, req_key.date_key, ship_key.date_key, "
        f"  od.unit_price, od.quantity, od.discount, "
        f"  od.unit_price * od.quantity AS gross_amount, "
        f"  od.unit_price * od.quantity * od.discount AS discount_amount, "
        f"  od.unit_price * od.quantity - od.unit_price * od.quantity * od.discount AS net_amount, "
        f"  o.freight "
        f"FROM tmp_order_details_nov od "
        f"JOIN tmp_orders_nov o ON od.order_id = o.order_id "
        f"JOIN dwa_dim_customer c ON o.customer_id = c.customer_id "
        f"JOIN dwa_dim_product p ON od.product_id = p.product_id "
        f"LEFT JOIN dwa_dim_employee e ON o.employee_id = e.employee_id "
        f"LEFT JOIN dwa_dim_shipper sh ON o.ship_via = sh.shipper_id "
        f"LEFT JOIN dwa_dim_geography g "
        f"  ON g.geography_signature = {_GEO_SIG_EXPR} "
        f"LEFT JOIN dwa_dim_date od_key ON CAST(o.order_date AS DATE) = od_key.full_date "
        f"LEFT JOIN dwa_dim_date req_key ON CAST(o.required_date AS DATE) = req_key.full_date "
        f"LEFT JOIN dwa_dim_date ship_key ON CAST(o.shipped_date AS DATE) = ship_key.full_date "
        f"ON CONFLICT (order_id, product_id) DO NOTHING"
    ))
    return result.rowcount


async def run(session):
    await _check_integridad_nov(session)

    resumen = {}
    inicio_total = _now()

    # 1. Nuevas fechas
    t0 = _now()
    n_fechas = await _insertar_fechas_nuevas(session)
    resumen["fechas_nuevas"] = n_fechas
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_dim_date", "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME, "fecha_inicio": t0, "fecha_fin": _now(),
        "registros_procesados": n_fechas, "estado": "OK",
        "observaciones": "Fechas nuevas de Ingesta2",
    })

    # 2. Nuevas geografias de envio
    t0 = _now()
    n_geos = await _insertar_geografias_nuevas(session)
    resumen["geografias_nuevas"] = n_geos
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_dim_geography", "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME, "fecha_inicio": t0, "fecha_fin": _now(),
        "registros_procesados": n_geos, "estado": "OK",
        "observaciones": "Geografias de envio nuevas de Ingesta2",
    })

    # 3. SCD2 customers
    t0 = _now()
    res_cust = await _aplicar_scd2_customers(session)
    resumen["customers_scd2"] = res_cust
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_dim_customer", "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME, "fecha_inicio": t0, "fecha_fin": _now(),
        "registros_procesados": len(res_cust["modificados"]), "estado": "OK",
        "observaciones": f"SCD2 aplicado a: {res_cust['modificados']}",
    })

    # 4. SCD2 products
    t0 = _now()
    res_prod = await _aplicar_scd2_products(session)
    resumen["products_scd2"] = res_prod
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_dim_product", "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME, "fecha_inicio": t0, "fecha_fin": _now(),
        "registros_procesados": len(res_prod["modificados"]), "estado": "OK",
        "observaciones": f"SCD2 aplicado a productos: {res_prod['modificados']}",
    })

    # 5. Nuevas lineas de hecho
    t0 = _now()
    n_fact = await _insertar_nuevas_ordenes(session)
    resumen["lineas_hecho_nuevas"] = n_fact
    await session.execute(_INSERT_EVENTO, {
        "tabla": "dwa_fact_order_lines", "tipo_evento": "ACTUALIZACION_DWA",
        "nombre_script": NAME, "fecha_inicio": t0, "fecha_fin": _now(),
        "registros_procesados": n_fact, "estado": "OK",
        "observaciones": "Nuevas lineas de orden de Ingesta2",
    })

    resumen["total_segundos"] = (_now() - inicio_total).total_seconds()
    return resumen
