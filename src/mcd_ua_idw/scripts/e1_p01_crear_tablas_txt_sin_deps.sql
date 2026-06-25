-- Nombre: e1_p01_crear_tablas_txt_sin_deps
-- Descripcion: Crea las tablas TXT_ para las 5 entidades sin dependencias FK
--              (categories, suppliers, shippers, regions, customers).
--              Todos los campos son TEXT — copia fiel del CSV sin conversion de tipos.
--              Sin claves primarias: el area TXT es raw storage, no se valida estructura.
-- Fecha: 2026-06-23
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar ANTES de e1_p03_cargar_txt_sin_deps (que escribe en estas tablas).

DROP TABLE IF EXISTS txt_categories;
CREATE TABLE txt_categories (
    category_id    TEXT,
    category_name  TEXT,
    description    TEXT,
    picture        TEXT
);

DROP TABLE IF EXISTS txt_suppliers;
CREATE TABLE txt_suppliers (
    supplier_id    TEXT,
    company_name   TEXT,
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

DROP TABLE IF EXISTS txt_shippers;
CREATE TABLE txt_shippers (
    shipper_id    TEXT,
    company_name  TEXT,
    phone         TEXT
);

DROP TABLE IF EXISTS txt_regions;
CREATE TABLE txt_regions (
    region_id           TEXT,
    region_description  TEXT
);

DROP TABLE IF EXISTS txt_customers;
CREATE TABLE txt_customers (
    customer_id    TEXT,
    company_name   TEXT,
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
