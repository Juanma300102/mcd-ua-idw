-- Nombre: e3_p01_crear_tablas_txt_ingesta2
-- Descripcion: Crea las tablas TXT_ para las 4 tablas de novedades de Ingesta2
--              (customers_nov, products_nov, orders_nov, order_details_nov).
--              Todos los campos son TEXT — copia fiel del CSV sin conversion de tipos.
--              Se usan nombres _nov para no pisar las TXT_ de Ingesta1.
-- Fecha: 2026-06-29
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar ANTES de e3_p03_cargar_txt_ingesta2.

DROP TABLE IF EXISTS txt_customers_nov;
CREATE TABLE txt_customers_nov (
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

DROP TABLE IF EXISTS txt_products_nov;
CREATE TABLE txt_products_nov (
    product_id         TEXT,
    product_name       TEXT,
    supplier_id        TEXT,
    category_id        TEXT,
    quantity_per_unit  TEXT,
    unit_price         TEXT,
    units_in_stock     TEXT,
    units_on_order     TEXT,
    reorder_level      TEXT,
    discontinued       TEXT
);

DROP TABLE IF EXISTS txt_orders_nov;
CREATE TABLE txt_orders_nov (
    order_id         TEXT,
    customer_id      TEXT,
    employee_id      TEXT,
    order_date       TEXT,
    required_date    TEXT,
    shipped_date     TEXT,
    ship_via         TEXT,
    freight          TEXT,
    ship_name        TEXT,
    ship_address     TEXT,
    ship_city        TEXT,
    ship_region      TEXT,
    ship_postal_code TEXT,
    ship_country     TEXT
);

DROP TABLE IF EXISTS txt_order_details_nov;
CREATE TABLE txt_order_details_nov (
    order_id    TEXT,
    product_id  TEXT,
    unit_price  TEXT,
    quantity    TEXT,
    discount    TEXT
);
