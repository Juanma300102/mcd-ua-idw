-- Nombre: e3_p11_integrar_world_data
-- Descripcion: Agrega 6 columnas de enriquecimiento geografico a dwa_dim_geography
--              a partir de world-data-2023.csv (TP-10).
--              Columnas: country_iso_code, country_capital, country_language,
--              country_currency, country_latitude, country_longitude.
--              La carga de datos y el UPDATE la hace el wrapper Python.
-- Fecha: 2026-06-29
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar manualmente desde la TUI despues de e3_p10.
--       Este script solo modifica estructura; la carga la hace e3_p11.py.

DROP TABLE IF EXISTS txt_world_data;
CREATE TABLE txt_world_data (
    country          TEXT,
    iso_code         TEXT,
    capital          TEXT,
    official_language TEXT,
    currency_code    TEXT,
    latitude         TEXT,
    longitude        TEXT
);

ALTER TABLE dwa_dim_geography
    ADD COLUMN IF NOT EXISTS country_iso_code  TEXT,
    ADD COLUMN IF NOT EXISTS country_capital   TEXT,
    ADD COLUMN IF NOT EXISTS country_language  TEXT,
    ADD COLUMN IF NOT EXISTS country_currency  TEXT,
    ADD COLUMN IF NOT EXISTS country_latitude  NUMERIC,
    ADD COLUMN IF NOT EXISTS country_longitude NUMERIC;
