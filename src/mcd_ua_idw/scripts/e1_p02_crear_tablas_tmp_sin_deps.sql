-- Nombre: e1_p02_crear_tablas_tmp_sin_deps
-- Descripcion: Crea las tablas TMP_ para las 5 entidades sin dependencias FK
--              (categories, suppliers, shippers, regions, customers).
--              Tipos segun el DER de Northwind. Incluye claves primarias.
--              Los campos picture (categories) y photo (employees) se excluyen
--              de TMP_: son blobs OLE de SQL Server sin valor analitico.
-- Fecha: 2026-06-23
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar antes de los scripts de validacion (TP-3d/3e/3f) y de carga TXT->TMP (TP-3g).

DROP TABLE IF EXISTS tmp_categories;
CREATE TABLE tmp_categories (
    category_id    INTEGER PRIMARY KEY,
    category_name  TEXT NOT NULL,
    description    TEXT
    -- picture excluida: blob OLE de SQL Server sin uso analitico (ver decisiones_de_diseno.md)
);

DROP TABLE IF EXISTS tmp_suppliers;
CREATE TABLE tmp_suppliers (
    supplier_id    INTEGER PRIMARY KEY,
    company_name   TEXT NOT NULL,
    contact_name   TEXT,
    contact_title  TEXT,
    address        TEXT,
    city           TEXT,
    region         TEXT,
    postal_code    TEXT,
    country        TEXT,
    phone          TEXT,
    fax            TEXT,
    home_page      TEXT
);

DROP TABLE IF EXISTS tmp_shippers;
CREATE TABLE tmp_shippers (
    shipper_id    INTEGER PRIMARY KEY,
    company_name  TEXT NOT NULL,
    phone         TEXT
);

DROP TABLE IF EXISTS tmp_regions;
CREATE TABLE tmp_regions (
    region_id           INTEGER PRIMARY KEY,
    region_description  TEXT NOT NULL
);

DROP TABLE IF EXISTS tmp_customers;
CREATE TABLE tmp_customers (
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
