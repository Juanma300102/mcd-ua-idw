from sqlalchemy import text

NAME = "e1_p13_validar_integridad_ref"
VERSION = 1

_UMBRAL = 0.0  # TP-19: tolerancia cero

# (tabla_hija, col_fk, tabla_padre, col_pk)
_FK_CHECKS = [
    # tmp_employees.reports_to → tmp_employees.employee_id (auto-referencial)
    ("tmp_employees",            "reports_to",  "tmp_employees",  "employee_id"),
    # tmp_products
    ("tmp_products",             "supplier_id", "tmp_suppliers",  "supplier_id"),
    ("tmp_products",             "category_id", "tmp_categories", "category_id"),
    # tmp_territories
    ("tmp_territories",          "region_id",   "tmp_regions",    "region_id"),
    # tmp_employee_territories
    ("tmp_employee_territories", "employee_id", "tmp_employees",  "employee_id"),
    ("tmp_employee_territories", "territory_id","tmp_territories","territory_id"),
    # tmp_orders
    ("tmp_orders",               "customer_id", "tmp_customers",  "customer_id"),
    ("tmp_orders",               "employee_id", "tmp_employees",  "employee_id"),
    ("tmp_orders",               "ship_via",    "tmp_shippers",   "shipper_id"),
    # tmp_order_details
    ("tmp_order_details",        "order_id",    "tmp_orders",     "order_id"),
    ("tmp_order_details",        "product_id",  "tmp_products",   "product_id"),
]

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)


async def run(session):
    resultados = []

    for tabla_hija, col_fk, tabla_padre, col_pk in _FK_CHECKS:
        row = (await session.execute(text(
            f"SELECT COUNT(*) AS total, "
            f"COUNT(*) FILTER ("
            f"  WHERE {col_fk} IS NOT NULL "
            f"  AND {col_fk} NOT IN (SELECT {col_pk} FROM {tabla_padre})"
            f") AS huerfanos "
            f"FROM {tabla_hija}"
        ))).one()

        total = row.total
        huerfanos = row.huerfanos
        indicador = huerfanos / total if total > 0 else 0.0
        resultado = "OK" if huerfanos == 0 else "ERROR"
        col_display = f"{col_fk} → {tabla_padre}.{col_pk}"
        detalle = (
            f"FK {tabla_hija}.{col_fk} → {tabla_padre}.{col_pk}"
            if huerfanos == 0
            else f"FK {tabla_hija}.{col_fk} → {tabla_padre}.{col_pk}: {huerfanos} valor(es) huerfano(s)"
        )

        await session.execute(_INSERT_VAL, {
            "tabla": tabla_hija,
            "columna": col_display,
            "tipo_chequeo": "FK_INTEGRIDAD",
            "nombre_script": NAME,
            "total": total,
            "afectados": huerfanos,
            "indicador": indicador,
            "umbral": _UMBRAL,
            "resultado": resultado,
            "detalle": detalle,
        })

        resultados.append({
            "tabla": tabla_hija,
            "fk": col_display,
            "resultado": resultado,
            "huerfanos": huerfanos,
        })

    total_errores = sum(r["huerfanos"] for r in resultados)
    return {
        "checks_fk": len(resultados),
        "errores": total_errores,
        "detalle": [r for r in resultados if r["resultado"] == "ERROR"],
    }
