from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

NAME = "e4_p03_validar_productos_publicacion"
VERSION = 1

_UMBRAL = 0.0

_INSERT_VAL = text(
    "INSERT INTO dqm_validaciones "
    "(tabla, columna, tipo_chequeo, nombre_script, total_filas_evaluadas, "
    "registros_afectados, indicador_calculado, umbral_aplicado, resultado, detalle) "
    "VALUES (:tabla, :columna, :tipo_chequeo, :nombre_script, :total, "
    ":afectados, :indicador, :umbral, :resultado, :detalle)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _scalar(session, sql: str) -> Any:
    return (await session.execute(text(sql))).scalar_one()


async def _insert_check(
    session,
    *,
    tabla: str,
    columna: str | None,
    tipo: str,
    total: int,
    afectados: int,
    detalle_ok: str,
    detalle_error: str,
) -> dict[str, Any]:
    indicador = afectados / total if total > 0 else 0.0
    resultado = "OK" if afectados == 0 else "ERROR"
    detalle = detalle_ok if resultado == "OK" else detalle_error

    await session.execute(
        _INSERT_VAL,
        {
            "tabla": tabla,
            "columna": columna,
            "tipo_chequeo": tipo,
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
        "tipo_chequeo": tipo,
        "resultado": resultado,
        "registros_afectados": afectados,
    }


async def _refresh_own_dp02_summary(session) -> None:
    """Make the DQM dashboard product include the publication checks just run."""
    await session.execute(
        text("DELETE FROM dp02_dqm_validaciones_resumen WHERE nombre_script = :n"),
        {"n": NAME},
    )
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
            "WHERE nombre_script = :n "
            "AND fecha = (SELECT MAX(fecha) FROM dqm_validaciones WHERE nombre_script = :n) "
            "GROUP BY nombre_script, tabla, columna, tipo_chequeo, resultado"
        ),
        {"n": NAME},
    )


async def run(session):
    resultados = []

    dp01_rows = int(
        await _scalar(session, "SELECT COUNT(*) FROM dp01_ventas_geo_score")
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dp01_ventas_geo_score",
            columna=None,
            tipo="DP01_NO_VACIO",
            total=1,
            afectados=0 if dp01_rows > 0 else 1,
            detalle_ok=f"DP01 tiene {dp01_rows} fila(s) publicadas.",
            detalle_error="DP01 no tiene filas publicadas.",
        )
    )

    score_rows = int(
        await _scalar(
            session,
            "SELECT COUNT(*) FROM dp01_ventas_geo_score WHERE score_segment <> 'sin_score'",
        )
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dp01_ventas_geo_score",
            columna="score_segment",
            tipo="DP01_SCORE_ENRIQUECIDO",
            total=1,
            afectados=0 if score_rows > 0 else 1,
            detalle_ok=f"DP01 usa customer_score en {score_rows} fila(s) agregadas.",
            detalle_error="DP01 no tiene filas con customer_score; revisar e3_p12.",
        )
    )

    geo_missing = int(
        await _scalar(
            session,
            "SELECT COUNT(*) FROM dp01_ventas_geo_score "
            "WHERE country_iso_code IS NULL OR country_currency IS NULL "
            "OR country_latitude IS NULL OR country_longitude IS NULL",
        )
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dp01_ventas_geo_score",
            columna="country_iso_code|country_currency|country_latitude|country_longitude",
            tipo="DP01_GEOGRAFIA_ENRIQUECIDA",
            total=dp01_rows,
            afectados=geo_missing,
            detalle_ok="Todas las filas DP01 tienen geografia enriquecida minima para tablero.",
            detalle_error=f"Hay {geo_missing} fila(s) DP01 con geografia enriquecida incompleta.",
        )
    )

    metric_errors = int(
        await _scalar(
            session,
            "SELECT COUNT(*) FROM dp01_ventas_geo_score "
            "WHERE ordenes <= 0 OR lineas_orden <= 0 OR cantidad_total <= 0 OR net_amount < 0",
        )
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dp01_ventas_geo_score",
            columna="ordenes|lineas_orden|cantidad_total|net_amount",
            tipo="DP01_MEDIDAS_VALIDAS",
            total=dp01_rows,
            afectados=metric_errors,
            detalle_ok="Las medidas principales de DP01 son consistentes.",
            detalle_error=f"Hay {metric_errors} fila(s) DP01 con medidas invalidas.",
        )
    )

    previous_errors = int(
        await _scalar(
            session,
            "SELECT COUNT(*) FROM dqm_validaciones "
            "WHERE resultado = 'ERROR' AND nombre_script <> 'e4_p03_validar_productos_publicacion'",
        )
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dqm_validaciones",
            columna="resultado",
            tipo="DQM_SIN_ERRORES_PREVIOS",
            total=max(previous_errors, 1),
            afectados=0 if previous_errors == 0 else previous_errors,
            detalle_ok="No hay validaciones DQM previas en ERROR.",
            detalle_error=f"Existen {previous_errors} validacion(es) DQM previas en ERROR.",
        )
    )

    await _refresh_own_dp02_summary(session)

    empty_dqm_tables = int(
        await _scalar(
            session,
            "SELECT COUNT(*) FROM ("
            "  SELECT 'dp02_dqm_validaciones_resumen' AS tabla, COUNT(*) AS filas "
            "  FROM dp02_dqm_validaciones_resumen "
            "  UNION ALL "
            "  SELECT 'dp02_dqm_eventos_resumen', COUNT(*) FROM dp02_dqm_eventos_resumen "
            "  UNION ALL "
            "  SELECT 'dp02_dqm_perfilado_resumen', COUNT(*) FROM dp02_dqm_perfilado_resumen"
            ") t WHERE filas = 0",
        )
    )
    resultados.append(
        await _insert_check(
            session,
            tabla="dp02_dqm_*",
            columna=None,
            tipo="DP02_NO_VACIO",
            total=3,
            afectados=empty_dqm_tables,
            detalle_ok="Las tres tablas DP02 para tablero DQM tienen datos.",
            detalle_error=f"Hay {empty_dqm_tables} tabla(s) DP02 vacias.",
        )
    )

    await _refresh_own_dp02_summary(session)

    return {
        "validaciones": len(resultados),
        "errores": sum(1 for r in resultados if r["resultado"] == "ERROR"),
        "detalle": resultados,
    }
