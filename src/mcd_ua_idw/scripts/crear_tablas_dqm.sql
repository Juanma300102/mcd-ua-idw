-- Nombre: crear_tablas_dqm
-- Descripcion: Crea las tablas transversales de Data Quality Management:
--              dqm_eventos (huella de procesos de transformacion/copia),
--              dqm_validaciones (resultado de controles de calidad: formato,
--              PK, integridad referencial) y dqm_perfilado (estadisticas
--              descriptivas por tabla/columna).
-- Fecha: 2026-06-22
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1 (encabezado provisorio - formato final se confirma en otro punto de esta fase)

-- NOTA: este script se ejecuta via run_sql_file(session, path) desde Python.
-- El registro en Scripts/ScriptVersions/ScriptRuns lo hace runner.py
-- automaticamente; este .sql NO se autoregistra a si mismo.

DROP TABLE IF EXISTS dqm_eventos;
CREATE TABLE dqm_eventos (
    id                    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla                 TEXT NOT NULL,
    tipo_evento           TEXT NOT NULL,
    nombre_script         TEXT NOT NULL,
    fecha_inicio          TIMESTAMP,
    fecha_fin             TIMESTAMP,
    registros_procesados  INTEGER,
    estado                TEXT NOT NULL DEFAULT 'EN_PROCESO',
    observaciones         TEXT
);

DROP TABLE IF EXISTS dqm_validaciones;
CREATE TABLE dqm_validaciones (
    id                     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla                  TEXT NOT NULL,
    columna                TEXT,
    tipo_chequeo           TEXT NOT NULL,
    nombre_script          TEXT NOT NULL,
    fecha                  TIMESTAMP NOT NULL DEFAULT now(),
    total_filas_evaluadas  INTEGER,
    registros_afectados    INTEGER NOT NULL DEFAULT 0,
    indicador_calculado    NUMERIC,
    umbral_aplicado        NUMERIC,
    resultado              TEXT NOT NULL,
    detalle                TEXT
);

DROP TABLE IF EXISTS dqm_perfilado;
CREATE TABLE dqm_perfilado (
    id                   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla                TEXT NOT NULL,
    columna              TEXT,
    nombre_script        TEXT NOT NULL,
    fecha                TIMESTAMP NOT NULL DEFAULT now(),
    total_filas          INTEGER,
    nulos                INTEGER,
    valores_distintos    INTEGER,
    valor_minimo         TEXT,
    valor_maximo         TEXT,
    outliers_detectados  INTEGER,
    observaciones        TEXT
);
