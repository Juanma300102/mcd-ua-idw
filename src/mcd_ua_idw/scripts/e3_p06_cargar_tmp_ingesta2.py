from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e3_p06_cargar_tmp_ingesta2"
VERSION = 1

_TABLAS_TXT = [
    "txt_customers_nov",
    "txt_products_nov",
    "txt_orders_nov",
    "txt_order_details_nov",
]

_CARGAS = [
    (
        "txt_customers_nov",
        "tmp_customers_nov",
        text(
            "INSERT INTO tmp_customers_nov "
            "(customer_id, company_name, contact_name, contact_title, address, city, "
            "region, postal_code, country, phone, fax) "
            "SELECT customer_id, company_name, contact_name, contact_title, address, city, "
            "region, postal_code, country, phone, fax "
            "FROM txt_customers_nov"
        ),
    ),
    (
        "txt_products_nov",
        "tmp_products_nov",
        text(
            "INSERT INTO tmp_products_nov "
            "(product_id, product_name, supplier_id, category_id, quantity_per_unit, "
            "unit_price, units_in_stock, units_on_order, reorder_level, discontinued) "
            "SELECT "
            "CAST(product_id AS INTEGER), product_name, "
            "CAST(supplier_id AS INTEGER), CAST(category_id AS INTEGER), "
            "quantity_per_unit, CAST(unit_price AS NUMERIC), "
            "CAST(units_in_stock AS INTEGER), CAST(units_on_order AS INTEGER), "
            "CAST(reorder_level AS INTEGER), CAST(discontinued AS INTEGER) "
            "FROM txt_products_nov"
        ),
    ),
    (
        "txt_orders_nov",
        "tmp_orders_nov",
        text(
            "INSERT INTO tmp_orders_nov "
            "(order_id, customer_id, employee_id, order_date, required_date, "
            "shipped_date, ship_via, freight, ship_name, ship_address, "
            "ship_city, ship_region, ship_postal_code, ship_country) "
            "SELECT "
            "CAST(order_id AS INTEGER), customer_id, CAST(employee_id AS INTEGER), "
            "CAST(order_date AS TIMESTAMP), CAST(required_date AS TIMESTAMP), "
            "CAST(shipped_date AS TIMESTAMP), CAST(ship_via AS INTEGER), "
            "CAST(freight AS NUMERIC), ship_name, ship_address, "
            "ship_city, ship_region, ship_postal_code, ship_country "
            "FROM txt_orders_nov"
        ),
    ),
    (
        "txt_order_details_nov",
        "tmp_order_details_nov",
        text(
            "INSERT INTO tmp_order_details_nov "
            "(order_id, product_id, unit_price, quantity, discount) "
            "SELECT "
            "CAST(order_id AS INTEGER), CAST(product_id AS INTEGER), "
            "CAST(unit_price AS NUMERIC), CAST(quantity AS INTEGER), "
            "CAST(discount AS NUMERIC) "
            "FROM txt_order_details_nov"
        ),
    ),
]

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, :estado)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _check_validaciones(session) -> None:
    rows = (await session.execute(text(
        "SELECT tabla, columna, tipo_chequeo, detalle "
        "FROM dqm_validaciones "
        "WHERE resultado = 'ERROR' AND tabla = ANY(:tablas)"
    ), {"tablas": _TABLAS_TXT})).fetchall()

    if rows:
        detalle = "; ".join(
            f"{r.tabla}.{r.columna} [{r.tipo_chequeo}]: {r.detalle}" for r in rows
        )
        raise RuntimeError(
            f"Hay {len(rows)} validacion(es) con ERROR en dqm_validaciones. "
            f"Corregir antes de cargar TMP_. Detalle: {detalle}"
        )


async def _check_idempotencia(session) -> None:
    for _, tmp_tabla, _ in _CARGAS:
        count = (await session.execute(
            text(f"SELECT COUNT(*) FROM {tmp_tabla}")
        )).scalar()
        if count > 0:
            raise RuntimeError(
                f"{tmp_tabla} ya tiene {count} fila(s). "
                "Truncar las tablas TMP_nov manualmente antes de volver a cargar."
            )


async def run(session):
    await _check_validaciones(session)
    await _check_idempotencia(session)

    filas_cargadas = {}

    for txt_tabla, tmp_tabla, insert_sql in _CARGAS:
        inicio = _now()
        result = await session.execute(insert_sql)
        fin = _now()

        filas = result.rowcount
        filas_cargadas[tmp_tabla] = filas

        await session.execute(_INSERT_EVENTO, {
            "tabla": tmp_tabla,
            "tipo_evento": "CARGA_TMP",
            "nombre_script": NAME,
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "registros_procesados": filas,
            "estado": "OK",
        })

    return {"filas_cargadas": filas_cargadas}
