-- Nombre: e1_p08_crear_tablas_tmp_con_deps
-- Descripcion: Crea las tablas TMP_ para las 6 entidades con dependencias FK
--              (employees, products, territories, employee_territories, orders, order_details).
--              Tipos segun el DER de Northwind. Incluye claves primarias (simples y compuestas).
--              photo (employees) excluida: blob OLE sin valor analitico.
--              No se definen FK constraints: la integridad referencial se valida en e1_p13.
-- Fecha: 2026-06-23
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar antes de e1_p09 (carga TXT_) y e1_p12 (carga TMP_).

DROP TABLE IF EXISTS tmp_order_details;
DROP TABLE IF EXISTS tmp_employee_territories;
DROP TABLE IF EXISTS tmp_orders;
DROP TABLE IF EXISTS tmp_products;
DROP TABLE IF EXISTS tmp_territories;
DROP TABLE IF EXISTS tmp_employees;

CREATE TABLE tmp_employees (
    employee_id        INTEGER PRIMARY KEY,
    last_name          TEXT NOT NULL,
    first_name         TEXT NOT NULL,
    title              TEXT,
    title_of_courtesy  TEXT,
    birth_date         TIMESTAMP,
    hire_date          TIMESTAMP,
    address            TEXT,
    city               TEXT,
    region             TEXT,
    postal_code        TEXT,
    country            TEXT,
    home_phone         TEXT,
    extension          TEXT,
    notes              TEXT,
    reports_to         INTEGER,  -- FK autorreferencial nullable (gerente general = NULL)
    photo_path         TEXT
    -- photo excluida: blob OLE de SQL Server sin uso analitico
);

CREATE TABLE tmp_products (
    product_id        INTEGER PRIMARY KEY,
    product_name      TEXT NOT NULL,
    supplier_id       INTEGER,
    category_id       INTEGER,
    quantity_per_unit TEXT,
    unit_price        NUMERIC,
    units_in_stock    INTEGER,
    units_on_order    INTEGER,
    reorder_level     INTEGER,
    discontinued      INTEGER  -- 0/1, no BOOLEAN (restriccion TP-23 SQL estandar)
);

CREATE TABLE tmp_territories (
    territory_id          TEXT PRIMARY KEY,  -- TEXT por ceros a la izquierda (ej. '01581')
    territory_description TEXT NOT NULL,
    region_id             INTEGER
);

CREATE TABLE tmp_employee_territories (
    employee_id  INTEGER,
    territory_id TEXT,           -- TEXT para coincidir con tmp_territories.territory_id
    PRIMARY KEY (employee_id, territory_id)
);

CREATE TABLE tmp_orders (
    order_id         INTEGER PRIMARY KEY,
    customer_id      TEXT,
    employee_id      INTEGER,
    order_date       TIMESTAMP,
    required_date    TIMESTAMP,
    shipped_date     TIMESTAMP,  -- nullable: ordenes sin despachar
    ship_via         INTEGER,
    freight          NUMERIC,
    ship_name        TEXT,
    ship_address     TEXT,
    ship_city        TEXT,
    ship_region      TEXT,       -- nullable: pedidos sin region de envio
    ship_postal_code TEXT,
    ship_country     TEXT
);

CREATE TABLE tmp_order_details (
    order_id   INTEGER,
    product_id INTEGER,
    PRIMARY KEY (order_id, product_id),
    unit_price NUMERIC,
    quantity   INTEGER,
    discount   NUMERIC
);
