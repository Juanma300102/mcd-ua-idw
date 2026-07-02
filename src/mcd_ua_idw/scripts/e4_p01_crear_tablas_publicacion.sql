-- Nombre: e4_p01_crear_tablas_publicacion
-- Descripcion: Crea productos de datos DPxx para Etapa 4:
--              DP01 ventas por geografia/score y DP02 resumen DQM para tablero.
-- Fecha: 2026-07-02
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar manualmente desde la TUI despues de verificar Etapa 3.
--       Este script solo crea estructura; la carga la hace e4_p02.py.

DROP TABLE IF EXISTS dp02_dqm_perfilado_resumen;
DROP TABLE IF EXISTS dp02_dqm_eventos_resumen;
DROP TABLE IF EXISTS dp02_dqm_validaciones_resumen;
DROP TABLE IF EXISTS dp01_ventas_geo_score;

CREATE TABLE dp01_ventas_geo_score (
    anio                    INTEGER NOT NULL,
    mes                     INTEGER NOT NULL,
    periodo                 TEXT NOT NULL,
    ship_country            TEXT NOT NULL,
    country_iso_code        TEXT,
    country_capital         TEXT,
    country_language        TEXT,
    country_currency        TEXT,
    country_latitude        NUMERIC,
    country_longitude       NUMERIC,
    score_segment           TEXT NOT NULL,
    score_segment_order     INTEGER NOT NULL,
    clientes_distintos      INTEGER NOT NULL,
    ordenes                 INTEGER NOT NULL,
    lineas_orden            INTEGER NOT NULL,
    cantidad_total          INTEGER NOT NULL,
    gross_amount            NUMERIC NOT NULL,
    discount_amount         NUMERIC NOT NULL,
    net_amount              NUMERIC NOT NULL,
    avg_order_net_amount    NUMERIC,
    fecha_publicacion       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (anio, mes, ship_country, score_segment)
);

CREATE TABLE dp02_dqm_validaciones_resumen (
    nombre_script              TEXT NOT NULL,
    tabla                      TEXT NOT NULL,
    columna                    TEXT,
    tipo_chequeo               TEXT NOT NULL,
    resultado                  TEXT NOT NULL,
    checks                     INTEGER NOT NULL,
    registros_afectados_total  INTEGER NOT NULL,
    indicador_maximo           NUMERIC,
    umbral_maximo              NUMERIC,
    ultima_fecha               TIMESTAMP,
    fecha_publicacion          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dp02_dqm_eventos_resumen (
    nombre_script              TEXT NOT NULL,
    tabla                      TEXT NOT NULL,
    tipo_evento                TEXT NOT NULL,
    estado                     TEXT NOT NULL,
    eventos                    INTEGER NOT NULL,
    registros_procesados_total INTEGER,
    primera_ejecucion          TIMESTAMP,
    ultima_ejecucion           TIMESTAMP,
    fecha_publicacion          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dp02_dqm_perfilado_resumen (
    tabla                      TEXT NOT NULL,
    columnas_perfiladas        INTEGER NOT NULL,
    total_filas_maximo         INTEGER,
    nulos_total                INTEGER,
    valores_distintos_total    INTEGER,
    outliers_total             INTEGER,
    ultima_fecha               TIMESTAMP,
    fecha_publicacion          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
