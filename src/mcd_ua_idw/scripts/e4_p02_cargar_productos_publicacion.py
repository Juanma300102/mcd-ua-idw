from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e4_p02_cargar_productos_publicacion"
VERSION = 1

_DP_TABLES = [
    "dp01_ventas_geo_score",
    "dp02_dqm_validaciones_resumen",
    "dp02_dqm_eventos_resumen",
    "dp02_dqm_perfilado_resumen",
]

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado, observaciones) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, 'OK', :observaciones)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _count_table(session, table_name: str) -> int:
    return (
        await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    ).scalar_one()


async def _log_event(
    session, table_name: str, start: datetime, rows: int, obs: str
) -> None:
    await session.execute(
        _INSERT_EVENTO,
        {
            "tabla": table_name,
            "tipo_evento": "PUBLICACION_DP",
            "nombre_script": NAME,
            "fecha_inicio": start,
            "fecha_fin": _now(),
            "registros_procesados": rows,
            "observaciones": obs,
        },
    )


async def run(session):
    resumen: dict[str, int] = {}

    for table_name in _DP_TABLES:
        await session.execute(text(f"DELETE FROM {table_name}"))

    t0 = _now()
    await session.execute(
        text(
            "INSERT INTO dp01_ventas_geo_score ("
            "anio, mes, periodo, ship_country, country_iso_code, country_capital, "
            "country_language, country_currency, country_latitude, country_longitude, "
            "score_segment, score_segment_order, clientes_distintos, ordenes, "
            "lineas_orden, cantidad_total, gross_amount, discount_amount, "
            "net_amount, avg_order_net_amount"
            ") "
            "SELECT "
            "  d.year_number AS anio, "
            "  d.month_number AS mes, "
            "  CAST(d.year_number AS TEXT) || '-' || LPAD(CAST(d.month_number AS TEXT), 2, '0') AS periodo, "
            "  COALESCE(g.country, '<sin_pais>') AS ship_country, "
            "  g.country_iso_code, g.country_capital, g.country_language, g.country_currency, "
            "  g.country_latitude, g.country_longitude, "
            "  CASE "
            "    WHEN sc.score IS NULL THEN 'sin_score' "
            "    WHEN sc.score >= 4 THEN 'alto_4_5' "
            "    WHEN sc.score >= 2 THEN 'medio_2_3' "
            "    ELSE 'bajo_0_1' "
            "  END AS score_segment, "
            "  CASE "
            "    WHEN sc.score IS NULL THEN 4 "
            "    WHEN sc.score >= 4 THEN 1 "
            "    WHEN sc.score >= 2 THEN 2 "
            "    ELSE 3 "
            "  END AS score_segment_order, "
            "  CAST(COUNT(DISTINCT f.customer_key) AS INTEGER) AS clientes_distintos, "
            "  CAST(COUNT(DISTINCT f.order_id) AS INTEGER) AS ordenes, "
            "  CAST(COUNT(*) AS INTEGER) AS lineas_orden, "
            "  CAST(SUM(f.quantity) AS INTEGER) AS cantidad_total, "
            "  SUM(f.gross_amount) AS gross_amount, "
            "  SUM(f.discount_amount) AS discount_amount, "
            "  SUM(f.net_amount) AS net_amount, "
            "  SUM(f.net_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_net_amount "
            "FROM dwa_fact_order_lines f "
            "JOIN dwa_dim_date d ON d.date_key = f.order_date_key "
            "JOIN dwa_dim_geography g ON g.geography_key = f.ship_geography_key "
            "JOIN dwa_dim_customer c ON c.customer_key = f.customer_key "
            "LEFT JOIN dwa_enr_customer_score sc ON sc.customer_key = c.customer_key "
            "GROUP BY d.year_number, d.month_number, g.country, g.country_iso_code, "
            "g.country_capital, g.country_language, g.country_currency, "
            "g.country_latitude, g.country_longitude, score_segment, score_segment_order"
        )
    )
    resumen["dp01_ventas_geo_score"] = await _count_table(
        session, "dp01_ventas_geo_score"
    )
    await _log_event(
        session,
        "dp01_ventas_geo_score",
        t0,
        resumen["dp01_ventas_geo_score"],
        "Producto DP01: ventas por mes, geografia de envio y segmento de customer_score.",
    )

    t0 = _now()
    await session.execute(
        text(
            "INSERT INTO dp02_dqm_validaciones_resumen ("
            "nombre_script, tabla, columna, tipo_chequeo, resultado, checks, "
            "registros_afectados_total, indicador_maximo, umbral_maximo, ultima_fecha"
            ") "
            "SELECT nombre_script, tabla, columna, tipo_chequeo, resultado, "
            "CAST(COUNT(*) AS INTEGER), "
            "CAST(COALESCE(SUM(registros_afectados), 0) AS INTEGER), "
            "MAX(indicador_calculado), MAX(umbral_aplicado), MAX(fecha) "
            "FROM dqm_validaciones "
            "GROUP BY nombre_script, tabla, columna, tipo_chequeo, resultado"
        )
    )
    resumen["dp02_dqm_validaciones_resumen"] = await _count_table(
        session, "dp02_dqm_validaciones_resumen"
    )
    await _log_event(
        session,
        "dp02_dqm_validaciones_resumen",
        t0,
        resumen["dp02_dqm_validaciones_resumen"],
        "Producto DP02: resumen de validaciones DQM para tablero.",
    )

    t0 = _now()
    await session.execute(
        text(
            "INSERT INTO dp02_dqm_eventos_resumen ("
            "nombre_script, tabla, tipo_evento, estado, eventos, registros_procesados_total, "
            "primera_ejecucion, ultima_ejecucion"
            ") "
            "SELECT nombre_script, tabla, tipo_evento, estado, "
            "CAST(COUNT(*) AS INTEGER), "
            "CAST(COALESCE(SUM(registros_procesados), 0) AS INTEGER), "
            "MIN(fecha_inicio), MAX(fecha_fin) "
            "FROM dqm_eventos "
            "GROUP BY nombre_script, tabla, tipo_evento, estado"
        )
    )
    resumen["dp02_dqm_eventos_resumen"] = await _count_table(
        session, "dp02_dqm_eventos_resumen"
    )
    await _log_event(
        session,
        "dp02_dqm_eventos_resumen",
        t0,
        resumen["dp02_dqm_eventos_resumen"],
        "Producto DP02: resumen de eventos DQM para tablero.",
    )

    t0 = _now()
    await session.execute(
        text(
            "INSERT INTO dp02_dqm_perfilado_resumen ("
            "tabla, columnas_perfiladas, total_filas_maximo, nulos_total, "
            "valores_distintos_total, outliers_total, ultima_fecha"
            ") "
            "SELECT tabla, "
            "CAST(COUNT(DISTINCT columna) AS INTEGER), "
            "CAST(MAX(total_filas) AS INTEGER), "
            "CAST(COALESCE(SUM(nulos), 0) AS INTEGER), "
            "CAST(COALESCE(SUM(valores_distintos), 0) AS INTEGER), "
            "CAST(COALESCE(SUM(outliers_detectados), 0) AS INTEGER), "
            "MAX(fecha) "
            "FROM dqm_perfilado "
            "GROUP BY tabla"
        )
    )
    resumen["dp02_dqm_perfilado_resumen"] = await _count_table(
        session, "dp02_dqm_perfilado_resumen"
    )
    if resumen["dp02_dqm_perfilado_resumen"] == 0:
        await session.execute(
            text(
                "INSERT INTO dp02_dqm_perfilado_resumen ("
                "tabla, columnas_perfiladas, total_filas_maximo, nulos_total, "
                "valores_distintos_total, outliers_total, ultima_fecha"
                ") VALUES ('sin_perfilado_disponible', 0, 0, 0, 0, 0, CURRENT_TIMESTAMP)"
            )
        )
        resumen["dp02_dqm_perfilado_resumen"] = 1
    await _log_event(
        session,
        "dp02_dqm_perfilado_resumen",
        t0,
        resumen["dp02_dqm_perfilado_resumen"],
        "Producto DP02: resumen de perfilado DQM para tablero.",
    )

    return resumen
