from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

NAME = "e4_p04_documentar_metadata_publicacion"
VERSION = 1

_PROCESOS = [
    (
        "e4_p01_crear_tablas_publicacion",
        "4",
        "01",
        "DDL",
        "DWA_DQM",
        "DPxx",
        "Crea productos de datos DP01/DP02 para publicacion.",
        33,
        0,
    ),
    (
        "e4_p02_cargar_productos_publicacion",
        "4",
        "02",
        "PUBLICACION_DP",
        "DWA_DQM",
        "DPxx",
        "Carga productos de datos para tableros.",
        34,
        1,
    ),
    (
        "e4_p03_validar_productos_publicacion",
        "4",
        "03",
        "DQM",
        "DPxx",
        "DQM",
        "Valida productos publicados y registra indicadores DQM.",
        35,
        1,
    ),
    (
        "e4_p04_documentar_metadata_publicacion",
        "4",
        "04",
        "METADATA",
        "DPxx",
        "MET",
        "Documenta entidades, procesos e indicadores de Etapa 4.",
        36,
        0,
    ),
    (
        "e4_p05_generar_tableros_html",
        "4",
        "05",
        "TABLERO",
        "DPxx",
        "DOCS",
        "Genera tableros HTML estaticos para DP01 y DQM.",
        37,
        0,
    ),
]

_ENTIDADES = [
    (
        "dp01_ventas_geo_score",
        "DPxx",
        "PRODUCTO_DATOS",
        "Ventas por periodo, geografia de envio y segmento de customer_score para tablero de negocio.",
        "1 fila por mes + pais de envio + segmento de score",
        "DWA fact/dimensiones + dwa_enr_customer_score",
    ),
    (
        "dp02_dqm_validaciones_resumen",
        "DPxx",
        "PRODUCTO_DATOS",
        "Resumen de validaciones DQM para tablero de calidad.",
        "1 fila por script + tabla + columna + chequeo + resultado",
        "dqm_validaciones",
    ),
    (
        "dp02_dqm_eventos_resumen",
        "DPxx",
        "PRODUCTO_DATOS",
        "Resumen de eventos DQM para tablero de calidad.",
        "1 fila por script + tabla + evento + estado",
        "dqm_eventos",
    ),
    (
        "dp02_dqm_perfilado_resumen",
        "DPxx",
        "PRODUCTO_DATOS",
        "Resumen de perfilado DQM para tablero de calidad.",
        "1 fila por tabla perfilada",
        "dqm_perfilado",
    ),
    (
        "tablero_dp01_ventas_geo_score.html",
        "DPxx",
        "TABLERO_HTML",
        "Tablero HTML estatico de ventas por geografia y score.",
        "Documento HTML generado desde DP01",
        "dp01_ventas_geo_score",
    ),
    (
        "tablero_dp02_dqm.html",
        "DPxx",
        "TABLERO_HTML",
        "Tablero HTML estatico de salud DQM.",
        "Documento HTML generado desde DP02",
        "dp02_dqm_*",
    ),
]

_ATRIBUTOS = [
    (
        "dp01_ventas_geo_score",
        "periodo",
        "TEXT",
        1,
        0,
        0,
        "Periodo mensual YYYY-MM del pedido.",
    ),
    (
        "dp01_ventas_geo_score",
        "ship_country",
        "TEXT",
        1,
        0,
        0,
        "Pais de envio usado para navegacion geografica.",
    ),
    (
        "dp01_ventas_geo_score",
        "country_iso_code",
        "TEXT",
        0,
        0,
        1,
        "Codigo ISO-2 de pais incorporado desde world-data-2023.",
    ),
    (
        "dp01_ventas_geo_score",
        "country_currency",
        "TEXT",
        0,
        0,
        1,
        "Moneda del pais incorporada desde world-data-2023.",
    ),
    (
        "dp01_ventas_geo_score",
        "country_latitude",
        "NUMERIC",
        0,
        0,
        1,
        "Latitud del pais para mapas.",
    ),
    (
        "dp01_ventas_geo_score",
        "country_longitude",
        "NUMERIC",
        0,
        0,
        1,
        "Longitud del pais para mapas.",
    ),
    (
        "dp01_ventas_geo_score",
        "score_segment",
        "TEXT",
        1,
        0,
        0,
        "Segmento derivado de customer_score: alto, medio, bajo o sin_score.",
    ),
    (
        "dp01_ventas_geo_score",
        "ordenes",
        "INTEGER",
        0,
        0,
        0,
        "Cantidad de ordenes distintas.",
    ),
    (
        "dp01_ventas_geo_score",
        "net_amount",
        "NUMERIC",
        0,
        0,
        0,
        "Ventas netas agregadas.",
    ),
    (
        "dp01_ventas_geo_score",
        "avg_order_net_amount",
        "NUMERIC",
        0,
        0,
        1,
        "Venta neta promedio por orden.",
    ),
    (
        "dp02_dqm_validaciones_resumen",
        "resultado",
        "TEXT",
        0,
        0,
        0,
        "Estado agregado de validaciones DQM.",
    ),
    (
        "dp02_dqm_validaciones_resumen",
        "registros_afectados_total",
        "INTEGER",
        0,
        0,
        0,
        "Total agregado de registros afectados.",
    ),
    (
        "dp02_dqm_eventos_resumen",
        "estado",
        "TEXT",
        0,
        0,
        0,
        "Estado agregado de eventos DQM.",
    ),
    (
        "dp02_dqm_eventos_resumen",
        "registros_procesados_total",
        "INTEGER",
        0,
        0,
        1,
        "Total agregado de registros procesados.",
    ),
    (
        "dp02_dqm_perfilado_resumen",
        "columnas_perfiladas",
        "INTEGER",
        0,
        0,
        0,
        "Cantidad de columnas perfiladas por tabla.",
    ),
]

_INDICADORES = [
    (
        "DP01_NO_VACIO",
        "dp01_ventas_geo_score",
        None,
        "DP01 debe publicar al menos una fila.",
        0.0,
        "DPxx",
        "Control de completitud del producto de datos principal.",
    ),
    (
        "DP01_SCORE_ENRIQUECIDO",
        "dp01_ventas_geo_score",
        "score_segment",
        "DP01 debe incluir segmentos derivados de customer_score.",
        0.0,
        "DPxx",
        "Garantiza uso de campos agregados en Ingesta2.",
    ),
    (
        "DP01_GEOGRAFIA_ENRIQUECIDA",
        "dp01_ventas_geo_score",
        "country_iso_code|country_currency|country_latitude|country_longitude",
        "DP01 debe tener geografia enriquecida minima para tablero.",
        0.0,
        "DPxx",
        "Garantiza uso de world-data-2023 en publicacion.",
    ),
    (
        "DP01_MEDIDAS_VALIDAS",
        "dp01_ventas_geo_score",
        "ordenes|lineas_orden|cantidad_total|net_amount",
        "Medidas publicadas deben ser positivas o no negativas segun corresponda.",
        0.0,
        "DPxx",
        "Control de consistencia de metricas publicadas.",
    ),
    (
        "DP02_NO_VACIO",
        "dp02_dqm_*",
        None,
        "Las tablas DP02 para tablero DQM deben tener datos.",
        0.0,
        "DPxx",
        "Control de disponibilidad del tablero DQM.",
    ),
    (
        "DQM_SIN_ERRORES_PREVIOS",
        "dqm_validaciones",
        "resultado",
        "No deben existir validaciones previas en ERROR al publicar.",
        0.0,
        "DQM",
        "Control global previo a publicacion.",
    ),
]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _exists(session, sql: str, params: dict[str, Any]) -> bool:
    return (await session.execute(text(sql), params)).fetchone() is not None


async def _entity_id(session, nombre: str) -> int:
    return (
        await session.execute(
            text("SELECT id FROM met_entidades WHERE nombre = :n"),
            {"n": nombre},
        )
    ).scalar_one()


async def run(session):
    t0 = _now()
    procesos = entidades = atributos = indicadores = 0

    for (
        nombre,
        etapa,
        paso,
        tipo,
        origen,
        destino,
        descripcion,
        orden,
        requiere,
    ) in _PROCESOS:
        if not await _exists(
            session,
            "SELECT 1 FROM met_procesos WHERE nombre_script = :n",
            {"n": nombre},
        ):
            await session.execute(
                text(
                    "INSERT INTO met_procesos "
                    "(nombre_script, etapa, paso, tipo_proceso, capa_origen, capa_destino, "
                    "descripcion, orden_ejecucion, requiere_validacion) "
                    "VALUES (:n, :e, :p, :t, :o, :d, :desc, :ord, :req)"
                ),
                {
                    "n": nombre,
                    "e": etapa,
                    "p": paso,
                    "t": tipo,
                    "o": origen,
                    "d": destino,
                    "desc": descripcion,
                    "ord": orden,
                    "req": requiere,
                },
            )
            procesos += 1

    for nombre, capa, tipo, descripcion, grano, fuente in _ENTIDADES:
        if not await _exists(
            session, "SELECT 1 FROM met_entidades WHERE nombre = :n", {"n": nombre}
        ):
            await session.execute(
                text(
                    "INSERT INTO met_entidades "
                    "(nombre, capa, tipo_entidad, descripcion, grano, fuente, activa) "
                    "VALUES (:n, :c, :t, :d, :g, :f, 1)"
                ),
                {
                    "n": nombre,
                    "c": capa,
                    "t": tipo,
                    "d": descripcion,
                    "g": grano,
                    "f": fuente,
                },
            )
            entidades += 1

    for (
        entidad,
        nombre_attr,
        tipo_dato,
        es_pk,
        es_fk,
        es_nullable,
        descripcion,
    ) in _ATRIBUTOS:
        entidad_id = await _entity_id(session, entidad)
        if not await _exists(
            session,
            "SELECT 1 FROM met_atributos WHERE entidad_id = :eid AND nombre_atributo = :a",
            {"eid": entidad_id, "a": nombre_attr},
        ):
            await session.execute(
                text(
                    "INSERT INTO met_atributos "
                    "(entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion) "
                    "VALUES (:eid, :a, :td, :pk, :fk, :nul, :desc)"
                ),
                {
                    "eid": entidad_id,
                    "a": nombre_attr,
                    "td": tipo_dato,
                    "pk": es_pk,
                    "fk": es_fk,
                    "nul": es_nullable,
                    "desc": descripcion,
                },
            )
            atributos += 1

    for tipo, entidad, atributo, regla, umbral, capa, descripcion in _INDICADORES:
        if not await _exists(
            session,
            "SELECT 1 FROM met_indicadores_calidad WHERE tipo_chequeo = :t AND entidad = :e",
            {"t": tipo, "e": entidad},
        ):
            await session.execute(
                text(
                    "INSERT INTO met_indicadores_calidad "
                    "(tipo_chequeo, entidad, atributo, regla, umbral_aplicado, capa, descripcion) "
                    "VALUES (:t, :e, :a, :r, :u, :c, :d)"
                ),
                {
                    "t": tipo,
                    "e": entidad,
                    "a": atributo,
                    "r": regla,
                    "u": umbral,
                    "c": capa,
                    "d": descripcion,
                },
            )
            indicadores += 1

    await session.execute(
        text(
            "INSERT INTO dqm_eventos "
            "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
            "registros_procesados, estado, observaciones) "
            "VALUES ('met_entidades', 'ACTUALIZACION_METADATA', :n, :fi, :ff, :rp, 'OK', :obs)"
        ),
        {
            "n": NAME,
            "fi": t0,
            "ff": _now(),
            "rp": procesos + entidades + atributos + indicadores,
            "obs": (
                f"Etapa 4: {procesos} procesos, {entidades} entidades, "
                f"{atributos} atributos y {indicadores} indicadores registrados."
            ),
        },
    )

    return {
        "procesos_registrados": procesos,
        "entidades_registradas": entidades,
        "atributos_registrados": atributos,
        "indicadores_registrados": indicadores,
    }
