-- Nombre: e1_p07_crear_tablas_txt_con_deps
-- Descripcion: Crea las tablas TXT_ para las 6 entidades con dependencias FK
--              (employees, products, territories, employee_territories, orders, order_details).
--              Todos los campos TEXT, sin PKs ni constraints. Copia fiel del CSV.
-- Fecha: 2026-06-23
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar antes de e1_p08 (TMP_) y e1_p09 (carga CSV).

DROP TABLE IF EXISTS txt_employees;
CREATE TABLE txt_employees (
    employee_id        TEXT,
    last_name          TEXT,
    first_name         TEXT,
    title              TEXT,
    title_of_courtesy  TEXT,
    birth_date         TEXT,
    hire_date          TEXT,
    address            TEXT,
    city               TEXT,
    region             TEXT,
    postal_code        TEXT,
    country            TEXT,
    home_phone         TEXT,
    extension          TEXT,
    photo              TEXT,
    notes              TEXT,
    reports_to         TEXT,
    photo_path         TEXT
);

DROP TABLE IF EXISTS txt_products;
CREATE TABLE txt_products (
    product_id        TEXT,
    product_name      TEXT,
    supplier_id       TEXT,
    category_id       TEXT,
    quantity_per_unit TEXT,
    unit_price        TEXT,
    units_in_stock    TEXT,
    units_on_order    TEXT,
    reorder_level     TEXT,
    discontinued      TEXT
);

DROP TABLE IF EXISTS txt_territories;
CREATE TABLE txt_territories (
    territory_id          TEXT,
    territory_description TEXT,
    region_id             TEXT
);

DROP TABLE IF EXISTS txt_employee_territories;
CREATE TABLE txt_employee_territories (
    employee_id  TEXT,
    territory_id TEXT
);

DROP TABLE IF EXISTS txt_orders;
CREATE TABLE txt_orders (
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

DROP TABLE IF EXISTS txt_order_details;
CREATE TABLE txt_order_details (
    order_id   TEXT,
    product_id TEXT,
    unit_price TEXT,
    quantity   TEXT,
    discount   TEXT
);
