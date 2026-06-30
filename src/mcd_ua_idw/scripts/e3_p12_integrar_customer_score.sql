-- Nombre: e3_p12_integrar_customer_score
-- Descripcion: Crea la tabla de staging txt_customer_score y la tabla de
--              enriquecimiento dwa_enr_customer_score (TP-11).
--              La carga de datos la hace el wrapper Python.
-- Fecha: 2026-06-29
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar manualmente desde la TUI despues de e3_p11.

DROP TABLE IF EXISTS txt_customer_score;
CREATE TABLE txt_customer_score (
    customer_id TEXT,
    score       TEXT
);

DROP TABLE IF EXISTS dwa_enr_customer_score;
CREATE TABLE dwa_enr_customer_score (
    customer_key  INTEGER NOT NULL,
    customer_id   TEXT    NOT NULL UNIQUE,
    score         INTEGER NOT NULL,
    fecha_carga   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_key) REFERENCES dwa_dim_customer(customer_key)
);
