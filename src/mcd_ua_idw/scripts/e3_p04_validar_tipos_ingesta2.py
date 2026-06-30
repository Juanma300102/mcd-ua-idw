from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e3_p04_validar_tipos_ingesta2"
VERSION = 1

_UMBRAL = 0.0  # TP-19: tolerancia cero

# (tabla, columna, tipo_chequeo)
_CHECKS = [
    # TP-3d: columnas que se castean a INTEGER en TMP_
    ("txt_customers_nov",     "customer_id",   "PK_NULOS"),
    ("txt_customers_nov",     "customer_id",   "PK_DUPLICADOS"),
    ("txt_customers_nov",     "company_name",  "NOT_NULL"),
    ("txt_products_nov",      "product_id",    "FORMATO_ENTERO"),
    ("txt_products_nov",      "product_id",    "PK_NULOS"),
    ("txt_products_nov",      "product_id",    "PK_DUPLICADOS"),
    ("txt_products_nov",      "product_name",  "NOT_NULL"),
    ("txt_products_nov",      "supplier_id",   "FORMATO_ENTERO"),
    ("txt_products_nov",      "category_id",   "FORMATO_ENTERO"),
    ("txt_products_nov",      "unit_price",    "FORMATO_NUMERICO"),
    ("txt_products_nov",      "units_in_stock","FORMATO_ENTERO"),
    ("txt_products_nov",      "units_on_order","FORMATO_ENTERO"),
    ("txt_products_nov",      "reorder_level", "FORMATO_ENTERO"),
    ("txt_products_nov",      "discontinued",  "FORMATO_ENTERO"),
    ("txt_orders_nov",        "order_id",      "FORMATO_ENTERO"),
    ("txt_orders_nov",        "order_id",      "PK_NULOS"),
    ("txt_orders_nov",        "order_id",      "PK_DUPLICADOS"),
    ("txt_orders_nov",        "customer_id",   "NOT_NULL"),
    ("txt_orders_nov",        "employee_id",   "FORMATO_ENTERO"),
    ("txt_orders_nov",        "order_date",    "FORMATO_TIMESTAMP"),
    ("txt_orders_nov",        "ship_via",      "FORMATO_ENTERO"),
    ("txt_orders_nov",        "freight",       "FORMATO_NUMERICO"),
    ("txt_order_details_nov", "order_id",      "FORMATO_ENTERO"),
    ("txt_order_details_nov", "product_id",    "FORMATO_ENTERO"),
    ("txt_order_details_nov", "unit_price",    "FORMATO_NUMERICO"),
    ("txt_order_details_nov", "quantity",      "FORMATO_ENTERO"),
    ("txt_order_details_nov", "discount",      "FORMATO_NUMERICO"),
]

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _run_check(session, tabla: str, col: str, tipo: str) -> dict:
    if tipo == "FORMATO_ENTERO":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL AND {col} !~ '^\\d+$') AS errores "
            f"FROM {tabla}"
        ))).one()
        detalle = f"Valores no casteables a INTEGER en {tabla}.{col}"
    elif tipo == "FORMATO_NUMERICO":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL AND {col} !~ '^\\d+(\\.\\d+)?$') AS errores "
            f"FROM {tabla}"
        ))).one()
        detalle = f"Valores no casteables a NUMERIC en {tabla}.{col}"
    elif tipo == "FORMATO_TIMESTAMP":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL "
            f"  AND {col} !~ '^\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}}\\.\\d{{3}}$') AS errores "
            f"FROM {tabla}"
        ))).one()
        detalle = f"Valores no casteables a TIMESTAMP en {tabla}.{col}"
    elif tipo == "NOT_NULL":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NULL) AS errores "
            f"FROM {tabla}"
        ))).one()
        detalle = f"Nulos en columna NOT NULL {tabla}.{col}"
    elif tipo == "PK_NULOS":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NULL) AS errores "
            f"FROM {tabla}"
        ))).one()
        detalle = f"Nulos en PK {tabla}.{col}"
    elif tipo == "PK_DUPLICADOS":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) - COUNT(DISTINCT {col}) AS errores "
            f"FROM {tabla} WHERE {col} IS NOT NULL"
        ))).one()
        detalle = f"Duplicados en PK {tabla}.{col}"
    else:
        raise ValueError(f"tipo_chequeo desconocido: {tipo}")

    total = row.total
    errores = row.errores
    indicador = errores / total if total > 0 else 0.0
    resultado = "OK" if errores == 0 else "ERROR"

    await session.execute(_INSERT_VAL, {
        "tabla": tabla,
        "columna": col,
        "tipo_chequeo": tipo,
        "nombre_script": NAME,
        "total": total,
        "afectados": errores,
        "indicador": indicador,
        "umbral": _UMBRAL,
        "resultado": resultado,
        "detalle": detalle if errores == 0 else f"{detalle}: {errores} registro(s)",
    })

    return {"tabla": tabla, "columna": col, "tipo": tipo, "resultado": resultado, "errores": errores}


async def run(session):
    resultados = []
    for tabla, col, tipo in _CHECKS:
        r = await _run_check(session, tabla, col, tipo)
        resultados.append(r)

    total_errores = sum(r["errores"] for r in resultados)
    por_tabla: dict[str, int] = {}
    for r in resultados:
        if r["resultado"] == "ERROR":
            por_tabla[r["tabla"]] = por_tabla.get(r["tabla"], 0) + 1

    return {
        "validaciones": len(resultados),
        "errores": total_errores,
        "tablas_con_error": por_tabla,
    }
