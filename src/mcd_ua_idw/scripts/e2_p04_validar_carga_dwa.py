from sqlalchemy import text

NAME = "e2_p04_validar_carga_dwa"
VERSION = 1

_UMBRAL = 0.0
_EXPECTED_CHECKS = 16

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)


async def _insert_validation(
    session,
    *,
    tabla: str,
    columna: str | None,
    tipo_chequeo: str,
    total: int,
    afectados: int,
    detalle_ok: str,
    detalle_error: str,
) -> dict[str, int | str | None]:
    indicador = afectados / total if total > 0 else 0.0
    resultado = "OK" if afectados == 0 else "ERROR"
    detalle = detalle_ok if afectados == 0 else detalle_error

    await session.execute(
        _INSERT_VAL,
        {
            "tabla": tabla,
            "columna": columna,
            "tipo_chequeo": tipo_chequeo,
            "nombre_script": NAME,
            "total": total,
            "afectados": afectados,
            "indicador": indicador,
            "umbral": _UMBRAL,
            "resultado": resultado,
            "detalle": detalle,
        },
    )

    return {
        "tabla": tabla,
        "columna": columna,
        "tipo_chequeo": tipo_chequeo,
        "resultado": resultado,
        "afectados": afectados,
    }


async def _validate_no_previous_errors(session) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE resultado = 'ERROR') AS errores "
                "FROM dqm_validaciones "
                "WHERE nombre_script IN ("
                "  'e1_p04_validar_tipos_sin_deps', "
                "  'e1_p10_validar_tipos_con_deps', "
                "  'e1_p13_validar_integridad_ref'"
                ")"
            )
        )
    ).one()
    afectados = row.errores
    detalle_error = f"Hay {row.errores} validacion(es) ERROR previas."
    total = row.total
    if row.total == 0:
        total = 1
        afectados = 1
        detalle_error = "No hay validaciones previas de Etapa 1 registradas."

    return await _insert_validation(
        session,
        tabla="DWA",
        columna=None,
        tipo_chequeo="DWA_SIN_ERRORES_PREVIOS",
        total=total,
        afectados=afectados,
        detalle_ok="No hay errores previos de Etapa 1 bloqueantes para DWA.",
        detalle_error=detalle_error,
    )


async def _validate_non_empty_source(
    session,
    *,
    tabla: str,
    detalle_nombre: str,
) -> dict[str, int | str | None]:
    total = (await session.execute(text(f"SELECT COUNT(*) FROM {tabla}"))).scalar_one()
    afectados = 1 if total == 0 else 0
    return await _insert_validation(
        session,
        tabla=tabla,
        columna=None,
        tipo_chequeo="DWA_FUENTE_NO_VACIA",
        total=1,
        afectados=afectados,
        detalle_ok=f"{detalle_nombre} tiene {total} fila(s) disponibles.",
        detalle_error=f"{detalle_nombre} no tiene filas para cargar el DWA.",
    )


async def _validate_join(
    session,
    *,
    tabla_hija: str,
    col_fk: str,
    tabla_padre: str,
    col_pk: str,
) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                f"SELECT COUNT(*) AS total, "
                f"COUNT(*) FILTER ("
                f"  WHERE h.{col_fk} IS NOT NULL "
                f"  AND p.{col_pk} IS NULL"
                f") AS huerfanos "
                f"FROM {tabla_hija} h "
                f"LEFT JOIN {tabla_padre} p ON h.{col_fk} = p.{col_pk}"
            )
        )
    ).one()
    col_display = f"{col_fk} -> {tabla_padre}.{col_pk}"
    return await _insert_validation(
        session,
        tabla=tabla_hija,
        columna=col_display,
        tipo_chequeo="DWA_JOIN_DIMENSION",
        total=row.total,
        afectados=row.huerfanos,
        detalle_ok=f"Join {tabla_hija}.{col_fk} -> {tabla_padre}.{col_pk} completo.",
        detalle_error=(
            f"Join {tabla_hija}.{col_fk} -> {tabla_padre}.{col_pk}: "
            f"{row.huerfanos} valor(es) sin dimension/fuente."
        ),
    )


async def _validate_required_date(
    session,
    *,
    tabla: str,
    columna: str,
) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                f"SELECT COUNT(*) AS total, "
                f"COUNT(*) FILTER (WHERE {columna} IS NULL) AS nulos "
                f"FROM {tabla}"
            )
        )
    ).one()
    return await _insert_validation(
        session,
        tabla=tabla,
        columna=columna,
        tipo_chequeo="DWA_FECHA_REQUERIDA",
        total=row.total,
        afectados=row.nulos,
        detalle_ok=f"{tabla}.{columna} no tiene nulos para dimension de fecha.",
        detalle_error=f"{tabla}.{columna} tiene {row.nulos} nulo(s).",
    )


async def _validate_required_text(
    session,
    *,
    tabla: str,
    columna: str,
    descripcion: str,
) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                f"SELECT COUNT(*) AS total, "
                f"COUNT(*) FILTER ("
                f"  WHERE NULLIF(TRIM(CAST({columna} AS TEXT)), '') IS NULL"
                f") AS nulos "
                f"FROM {tabla}"
            )
        )
    ).one()
    return await _insert_validation(
        session,
        tabla=tabla,
        columna=columna,
        tipo_chequeo="DWA_GEOGRAFIA_REQUERIDA",
        total=row.total,
        afectados=row.nulos,
        detalle_ok=f"{descripcion} disponible para dimension geografica.",
        detalle_error=f"{descripcion} tiene {row.nulos} valor(es) vacio(s).",
    )


async def _validate_fact_grain(session) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                "WITH duplicados AS ("
                "  SELECT order_id, product_id, COUNT(*) AS cantidad "
                "  FROM tmp_order_details "
                "  GROUP BY order_id, product_id "
                "  HAVING COUNT(*) > 1"
                ") "
                "SELECT "
                "  (SELECT COUNT(*) FROM tmp_order_details) AS total, "
                "  COALESCE(SUM(cantidad - 1), 0) AS duplicados "
                "FROM duplicados"
            )
        )
    ).one()
    return await _insert_validation(
        session,
        tabla="tmp_order_details",
        columna="order_id|product_id",
        tipo_chequeo="DWA_GRANO_FACT",
        total=row.total,
        afectados=row.duplicados,
        detalle_ok="El grano order_id + product_id es unico para cargar el hecho.",
        detalle_error=(
            "tmp_order_details tiene "
            f"{row.duplicados} fila(s) duplicada(s) en el grano del hecho."
        ),
    )


async def _validate_measures(session) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER ("
                "  WHERE unit_price IS NULL "
                "  OR quantity IS NULL "
                "  OR discount IS NULL "
                "  OR quantity <= 0 "
                "  OR discount < 0 "
                "  OR discount > 1"
                ") AS invalidas "
                "FROM tmp_order_details"
            )
        )
    ).one()
    return await _insert_validation(
        session,
        tabla="tmp_order_details",
        columna="unit_price|quantity|discount",
        tipo_chequeo="DWA_MEDIDA_VALIDA",
        total=row.total,
        afectados=row.invalidas,
        detalle_ok="Medidas base validas para calcular gross/discount/net amount.",
        detalle_error=f"Hay {row.invalidas} linea(s) con medidas invalidas.",
    )


async def _validate_stock(session) -> dict[str, int | str | None]:
    row = (
        await session.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER ("
                "  WHERE units_in_stock IS NULL "
                "  OR units_on_order IS NULL "
                "  OR reorder_level IS NULL "
                "  OR units_in_stock < 0 "
                "  OR units_on_order < 0 "
                "  OR reorder_level < 0"
                ") AS invalidas "
                "FROM tmp_products"
            )
        )
    ).one()
    return await _insert_validation(
        session,
        tabla="tmp_products",
        columna="units_in_stock|units_on_order|reorder_level",
        tipo_chequeo="DWA_STOCK_VALIDO",
        total=row.total,
        afectados=row.invalidas,
        detalle_ok="Atributos de stock validos para dimension de producto.",
        detalle_error=f"Hay {row.invalidas} producto(s) con stock invalido.",
    )


async def run(session):
    resultados = [
        await _validate_no_previous_errors(session),
        await _validate_non_empty_source(
            session,
            tabla="tmp_orders",
            detalle_nombre="tmp_orders",
        ),
        await _validate_non_empty_source(
            session,
            tabla="tmp_order_details",
            detalle_nombre="tmp_order_details",
        ),
        await _validate_join(
            session,
            tabla_hija="tmp_orders",
            col_fk="customer_id",
            tabla_padre="tmp_customers",
            col_pk="customer_id",
        ),
        await _validate_join(
            session,
            tabla_hija="tmp_orders",
            col_fk="employee_id",
            tabla_padre="tmp_employees",
            col_pk="employee_id",
        ),
        await _validate_join(
            session,
            tabla_hija="tmp_orders",
            col_fk="ship_via",
            tabla_padre="tmp_shippers",
            col_pk="shipper_id",
        ),
        await _validate_join(
            session,
            tabla_hija="tmp_order_details",
            col_fk="order_id",
            tabla_padre="tmp_orders",
            col_pk="order_id",
        ),
        await _validate_join(
            session,
            tabla_hija="tmp_order_details",
            col_fk="product_id",
            tabla_padre="tmp_products",
            col_pk="product_id",
        ),
        await _validate_required_date(
            session, tabla="tmp_orders", columna="order_date"
        ),
        await _validate_required_date(
            session, tabla="tmp_orders", columna="required_date"
        ),
        await _validate_required_text(
            session,
            tabla="tmp_customers",
            columna="country",
            descripcion="tmp_customers.country",
        ),
        await _validate_required_text(
            session,
            tabla="tmp_employees",
            columna="country",
            descripcion="tmp_employees.country",
        ),
        await _validate_required_text(
            session,
            tabla="tmp_orders",
            columna="ship_country",
            descripcion="tmp_orders.ship_country",
        ),
        await _validate_fact_grain(session),
        await _validate_measures(session),
        await _validate_stock(session),
    ]

    errores = [r for r in resultados if r["resultado"] == "ERROR"]
    return {
        "validaciones_insertadas": len(resultados),
        "validaciones_esperadas_minimas": _EXPECTED_CHECKS,
        "errores": len(errores),
        "detalle_errores": errores,
    }
