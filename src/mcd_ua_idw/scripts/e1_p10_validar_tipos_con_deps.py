from sqlalchemy import text

NAME = "e1_p10_validar_tipos_con_deps"
VERSION = 1

_UMBRAL = 0.0  # TP-19: tolerancia cero

# (tabla, columna, tipo_chequeo)
# Para PK compuesta: columna = "col1|col2" (separador | solo en PK_DUPLICADOS)
_CHECKS = [
    # TP-3d: FORMATO_ENTERO — columnas que se castean a INTEGER en TMP_
    ("txt_employees",            "employee_id",    "FORMATO_ENTERO"),
    ("txt_employees",            "reports_to",     "FORMATO_ENTERO"),  # nullable: solo no-NULL
    ("txt_products",             "product_id",     "FORMATO_ENTERO"),
    ("txt_products",             "supplier_id",    "FORMATO_ENTERO"),
    ("txt_products",             "category_id",    "FORMATO_ENTERO"),
    ("txt_products",             "units_in_stock", "FORMATO_ENTERO"),
    ("txt_products",             "units_on_order", "FORMATO_ENTERO"),
    ("txt_products",             "reorder_level",  "FORMATO_ENTERO"),
    ("txt_products",             "discontinued",   "FORMATO_ENTERO"),
    ("txt_territories",          "region_id",      "FORMATO_ENTERO"),
    ("txt_employee_territories", "employee_id",    "FORMATO_ENTERO"),
    ("txt_orders",               "order_id",       "FORMATO_ENTERO"),
    ("txt_orders",               "employee_id",    "FORMATO_ENTERO"),
    ("txt_orders",               "ship_via",       "FORMATO_ENTERO"),
    ("txt_order_details",        "order_id",       "FORMATO_ENTERO"),
    ("txt_order_details",        "product_id",     "FORMATO_ENTERO"),
    ("txt_order_details",        "quantity",       "FORMATO_ENTERO"),
    # TP-3d: FORMATO_NUMERICO — columnas NUMERIC en TMP_
    ("txt_products",      "unit_price", "FORMATO_NUMERICO"),
    ("txt_orders",        "freight",    "FORMATO_NUMERICO"),
    ("txt_order_details", "unit_price", "FORMATO_NUMERICO"),
    ("txt_order_details", "discount",   "FORMATO_NUMERICO"),
    # TP-3d: FORMATO_TIMESTAMP — columnas TIMESTAMP en TMP_
    ("txt_employees", "birth_date",    "FORMATO_TIMESTAMP"),
    ("txt_employees", "hire_date",     "FORMATO_TIMESTAMP"),
    ("txt_orders",    "order_date",    "FORMATO_TIMESTAMP"),
    ("txt_orders",    "required_date", "FORMATO_TIMESTAMP"),
    ("txt_orders",    "shipped_date",  "FORMATO_TIMESTAMP"),  # nullable: solo no-NULL
    # TP-3d: NOT_NULL — columnas NOT NULL en TMP_
    ("txt_employees",   "last_name",             "NOT_NULL"),
    ("txt_employees",   "first_name",            "NOT_NULL"),
    ("txt_products",    "product_name",          "NOT_NULL"),
    ("txt_territories", "territory_description", "NOT_NULL"),
    # TP-3e: PK_NULOS — cada columna de PK (incluidas las de PKs compuestas)
    ("txt_employees",            "employee_id",  "PK_NULOS"),
    ("txt_products",             "product_id",   "PK_NULOS"),
    ("txt_territories",          "territory_id", "PK_NULOS"),
    ("txt_employee_territories", "employee_id",  "PK_NULOS"),
    ("txt_employee_territories", "territory_id", "PK_NULOS"),
    ("txt_orders",               "order_id",     "PK_NULOS"),
    ("txt_order_details",        "order_id",     "PK_NULOS"),
    ("txt_order_details",        "product_id",   "PK_NULOS"),
    # TP-3e: PK_DUPLICADOS — simples y compuestas (| separa columnas en PK compuesta)
    ("txt_employees",            "employee_id",              "PK_DUPLICADOS"),
    ("txt_products",             "product_id",               "PK_DUPLICADOS"),
    ("txt_territories",          "territory_id",             "PK_DUPLICADOS"),
    ("txt_employee_territories", "employee_id|territory_id", "PK_DUPLICADOS"),
    ("txt_orders",               "order_id",                 "PK_DUPLICADOS"),
    ("txt_order_details",        "order_id|product_id",      "PK_DUPLICADOS"),
]

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)

_RE_ENTERO   = r"^\d+$"
_RE_NUMERICO = r"^\d+(\.\d+)?$"
_RE_TS       = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$"


async def _run_check(session, tabla: str, col: str, tipo: str) -> dict:
    if tipo == "FORMATO_ENTERO":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL AND {col} !~ :re) AS errores "
            f"FROM {tabla}"
        ), {"re": _RE_ENTERO})).one()
        detalle = f"Valores no casteables a INTEGER en {tabla}.{col}"

    elif tipo == "FORMATO_NUMERICO":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL AND {col} !~ :re) AS errores "
            f"FROM {tabla}"
        ), {"re": _RE_NUMERICO})).one()
        detalle = f"Valores no casteables a NUMERIC en {tabla}.{col}"

    elif tipo == "FORMATO_TIMESTAMP":
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER (WHERE {col} IS NOT NULL AND {col} !~ :re) AS errores "
            f"FROM {tabla}"
        ), {"re": _RE_TS})).one()
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
        cols = col.split("|")
        if len(cols) == 1:
            row = (await session.execute(text(
                f"SELECT COUNT(*) AS total, "
                f"COUNT(*) - COUNT(DISTINCT {col}) AS errores "
                f"FROM {tabla} WHERE {col} IS NOT NULL"
            ))).one()
        else:
            cols_str = ", ".join(cols)
            row = (await session.execute(text(
                f"SELECT COUNT(*) AS total, "
                f"COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT {cols_str} FROM {tabla}) _t) AS errores "
                f"FROM {tabla}"
            ))).one()
        detalle = f"Duplicados en PK ({col.replace('|', ', ')}) de {tabla}"

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
