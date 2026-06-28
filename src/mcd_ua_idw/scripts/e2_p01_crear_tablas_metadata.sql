-- Nombre: e2_p01_crear_tablas_metadata
-- Descripcion: Crea el soporte de Metadata para describir entidades,
--              atributos, procesos e indicadores de calidad del DWA.
-- Fecha: 2026-06-25
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar manualmente desde la TUI antes de documentar entidades.

DROP TABLE IF EXISTS met_indicadores_calidad;
DROP TABLE IF EXISTS met_procesos;
DROP TABLE IF EXISTS met_atributos;
DROP TABLE IF EXISTS met_entidades;

CREATE TABLE met_entidades (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE,
    capa            TEXT NOT NULL,
    tipo_entidad    TEXT NOT NULL,
    descripcion     TEXT NOT NULL,
    grano           TEXT,
    fuente          TEXT,
    activa          INTEGER NOT NULL DEFAULT 1,
    fecha_registro  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE met_atributos (
    id                    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entidad_id            INTEGER NOT NULL,
    nombre_atributo       TEXT NOT NULL,
    tipo_dato             TEXT NOT NULL,
    es_pk                 INTEGER NOT NULL DEFAULT 0,
    es_fk                 INTEGER NOT NULL DEFAULT 0,
    es_nullable           INTEGER NOT NULL DEFAULT 1,
    entidad_referencia    TEXT,
    atributo_referencia   TEXT,
    descripcion           TEXT NOT NULL,
    fecha_registro        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (entidad_id, nombre_atributo),
    FOREIGN KEY (entidad_id) REFERENCES met_entidades(id)
);

CREATE TABLE met_procesos (
    id                   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_script        TEXT NOT NULL UNIQUE,
    etapa                TEXT NOT NULL,
    paso                 TEXT NOT NULL,
    tipo_proceso         TEXT NOT NULL,
    capa_origen          TEXT,
    capa_destino         TEXT,
    descripcion          TEXT NOT NULL,
    orden_ejecucion      INTEGER,
    requiere_validacion  INTEGER NOT NULL DEFAULT 1,
    fecha_registro       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE met_indicadores_calidad (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo_chequeo      TEXT NOT NULL,
    entidad           TEXT NOT NULL,
    atributo          TEXT,
    regla             TEXT NOT NULL,
    umbral_aplicado   NUMERIC,
    capa              TEXT NOT NULL,
    descripcion       TEXT NOT NULL,
    activo            INTEGER NOT NULL DEFAULT 1,
    fecha_registro    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
