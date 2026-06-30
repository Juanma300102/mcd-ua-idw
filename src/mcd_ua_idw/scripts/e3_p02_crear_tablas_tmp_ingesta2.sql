-- Nombre: e3_p02_crear_tablas_tmp_ingesta2
-- Descripcion: Crea las tablas TMP_ para las 4 tablas de novedades de Ingesta2
--              con los tipos del DER de Northwind. Incluye claves primarias.
--              Sin FK fisicas — la integridad se valida con e3_p07.
-- Fecha: 2026-06-29
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar antes de e3_p04/p05/p06.

DROP TABLE IF EXISTS tmp_order_details_nov;
DROP TABLE IF EXISTS tmp_orders_nov;
DROP TABLE IF EXISTS tmp_customers_nov;
DROP TABLE IF EXISTS tmp_products_nov;

CREATE TABLE tmp_customers_nov (
    customer_id    TEXT PRIMARY KEY,
    company_name   TEXT NOT NULL,
    contact_name   TEXT,
    contact_title  TEXT,
    address        TEXT,
    city           TEXT,
    region         TEXT,
    postal_code    TEXT,
    country        TEXT,
    phone          TEXT,
    fax            TEXT
);

CREATE TABLE tmp_products_nov (
    product_id         INTEGER PRIMARY KEY,
    product_name       TEXT NOT NULL,
    supplier_id        INTEGER,
    category_id        INTEGER,
    quantity_per_unit  TEXT,
    unit_price         NUMERIC,
    units_in_stock     INTEGER,
    units_on_order     INTEGER,
    reorder_level      INTEGER,
    discontinued       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE tmp_orders_nov (
    order_id         INTEGER PRIMARY KEY,
    customer_id      TEXT NOT NULL,
    employee_id      INTEGER,
    order_date       TIMESTAMP,
    required_date    TIMESTAMP,
    shipped_date     TIMESTAMP,
    ship_via         INTEGER,
    freight          NUMERIC,
    ship_name        TEXT,
    ship_address     TEXT,
    ship_city        TEXT,
    ship_region      TEXT,
    ship_postal_code TEXT,
    ship_country     TEXT
);

CREATE TABLE tmp_order_details_nov (
    order_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    unit_price  NUMERIC NOT NULL,
    quantity    INTEGER NOT NULL,
    discount    NUMERIC NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
