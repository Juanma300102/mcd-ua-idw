from sqlalchemy import text

NAME = "e3_p07_validar_integridad_ingesta2"
VERSION = 1

_UMBRAL = 0.0  # TP-19: tolerancia cero

# (tabla_hija, col_fk, tabla_padre, col_pk, descripcion)
# Las novedades se validan contra las tablas TMP_ de Ingesta1 (ya en el DWA)
# y contra las otras novedades cuando hay dependencia interna.
_FK_CHECKS = [
    # customers_nov: no tiene FKs a validar en este modelo
    # products_nov: supplier y category deben existir en TMP_ de Ingesta1
    ("tmp_products_nov", "supplier_id", "tmp_suppliers",  "supplier_id"),
    ("tmp_products_nov", "category_id", "tmp_categories", "category_id"),
    # orders_nov: customer debe existir en TMP_ Ingesta1 O en tmp_customers_nov
    ("tmp_orders_nov",   "customer_id", "tmp_customers",  "customer_id"),
    # orders_nov: employee y shipper deben existir en Ingesta1
    ("tmp_orders_nov",   "employee_id", "tmp_employees",  "employee_id"),
    ("tmp_orders_nov",   "ship_via",    "tmp_shippers",   "shipper_id"),
    # order_details_nov: order_id debe estar en tmp_orders_nov (son órdenes nuevas)
    ("tmp_order_details_nov", "order_id",   "tmp_orders_nov", "order_id"),
    # order_details_nov: product_id debe existir en TMP_ Ingesta1 o en tmp_products_nov
    ("tmp_order_details_nov", "product_id", "tmp_products",   "product_id"),
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
            f"  AND {col_fk}::TEXT NOT IN (SELECT {col_pk}::TEXT FROM {tabla_padre})"
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
