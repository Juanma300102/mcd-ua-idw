-- Nombre: e2_p03_crear_modelo_dwa
-- Descripcion: Crea el modelo DWA dimensional inicial, las tablas de Memoria
--              DWM y las tablas de enriquecimiento derivadas para Etapa 2.
-- Fecha: 2026-06-28
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar manualmente desde la TUI despues de e2_p01/e2_p02.
--       Este script solo define estructura; la carga inicial la hace e2_p05.

DROP TABLE IF EXISTS dwa_enr_product_sales_metrics;
DROP TABLE IF EXISTS dwa_enr_customer_sales_metrics;
DROP TABLE IF EXISTS dwm_product_history;
DROP TABLE IF EXISTS dwm_customer_history;
DROP TABLE IF EXISTS dwa_fact_order_lines;
DROP TABLE IF EXISTS dwa_dim_shipper;
DROP TABLE IF EXISTS dwa_dim_employee;
DROP TABLE IF EXISTS dwa_dim_product;
DROP TABLE IF EXISTS dwa_dim_customer;
DROP TABLE IF EXISTS dwa_dim_geography;
DROP TABLE IF EXISTS dwa_dim_date;

CREATE TABLE dwa_dim_date (
    date_key       INTEGER PRIMARY KEY, -- YYYYMMDD
    full_date      DATE NOT NULL UNIQUE,
    year_number    INTEGER NOT NULL,
    quarter_number INTEGER NOT NULL,
    month_number   INTEGER NOT NULL,
    day_number     INTEGER NOT NULL
);

CREATE TABLE dwa_dim_geography (
    geography_key       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geography_signature TEXT NOT NULL UNIQUE,
    country             TEXT,
    region              TEXT,
    city                TEXT,
    postal_code         TEXT,
    fecha_carga         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dwa_dim_customer (
    customer_key           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id            TEXT NOT NULL UNIQUE,
    customer_geography_key INTEGER NOT NULL,
    company_name           TEXT NOT NULL,
    contact_name           TEXT,
    contact_title          TEXT,
    city                   TEXT,
    region                 TEXT,
    postal_code            TEXT,
    country                TEXT,
    phone                  TEXT,
    fax                    TEXT,
    fecha_carga            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_geography_key) REFERENCES dwa_dim_geography(geography_key)
);

CREATE TABLE dwa_dim_product (
    product_key       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id        INTEGER NOT NULL UNIQUE,
    product_name      TEXT NOT NULL,
    category_id       INTEGER,
    category_name     TEXT,
    supplier_id       INTEGER,
    supplier_name     TEXT,
    quantity_per_unit TEXT,
    unit_price        NUMERIC,
    units_in_stock    INTEGER,
    units_on_order    INTEGER,
    reorder_level     INTEGER,
    discontinued      INTEGER,
    stock_alarm_level INTEGER NOT NULL DEFAULT 0,
    fecha_carga       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dwa_dim_employee (
    employee_key           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id            INTEGER NOT NULL UNIQUE,
    employee_geography_key INTEGER NOT NULL,
    employee_name          TEXT NOT NULL,
    title                  TEXT,
    city                   TEXT,
    region                 TEXT,
    country                TEXT,
    reports_to             INTEGER,
    fecha_carga            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_geography_key) REFERENCES dwa_dim_geography(geography_key)
);

CREATE TABLE dwa_dim_shipper (
    shipper_key  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipper_id   INTEGER NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    phone        TEXT,
    fecha_carga  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dwa_fact_order_lines (
    order_line_key       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id             INTEGER NOT NULL,
    product_id           INTEGER NOT NULL,
    customer_key         INTEGER NOT NULL,
    product_key          INTEGER NOT NULL,
    employee_key         INTEGER NOT NULL,
    shipper_key          INTEGER NOT NULL,
    ship_geography_key   INTEGER NOT NULL,
    order_date_key       INTEGER NOT NULL,
    required_date_key    INTEGER NOT NULL,
    shipped_date_key     INTEGER,
    unit_price           NUMERIC NOT NULL,
    quantity             INTEGER NOT NULL,
    discount             NUMERIC NOT NULL,
    gross_amount         NUMERIC NOT NULL,
    discount_amount      NUMERIC NOT NULL,
    net_amount           NUMERIC NOT NULL,
    order_freight_amount NUMERIC,
    fecha_carga          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (order_id, product_id),
    FOREIGN KEY (customer_key) REFERENCES dwa_dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dwa_dim_product(product_key),
    FOREIGN KEY (employee_key) REFERENCES dwa_dim_employee(employee_key),
    FOREIGN KEY (shipper_key) REFERENCES dwa_dim_shipper(shipper_key),
    FOREIGN KEY (ship_geography_key) REFERENCES dwa_dim_geography(geography_key),
    FOREIGN KEY (order_date_key) REFERENCES dwa_dim_date(date_key),
    FOREIGN KEY (required_date_key) REFERENCES dwa_dim_date(date_key),
    FOREIGN KEY (shipped_date_key) REFERENCES dwa_dim_date(date_key)
);

CREATE TABLE dwm_customer_history (
    customer_history_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id          TEXT NOT NULL,
    company_name         TEXT NOT NULL,
    contact_name         TEXT,
    contact_title        TEXT,
    city                 TEXT,
    region               TEXT,
    postal_code          TEXT,
    country              TEXT,
    phone                TEXT,
    fax                  TEXT,
    attribute_signature  TEXT NOT NULL,
    vigente_desde        TIMESTAMP NOT NULL,
    vigente_hasta        TIMESTAMP,
    es_vigente           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE dwm_product_history (
    product_history_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id          INTEGER NOT NULL,
    product_name        TEXT NOT NULL,
    category_id         INTEGER,
    category_name       TEXT,
    supplier_id         INTEGER,
    supplier_name       TEXT,
    quantity_per_unit   TEXT,
    unit_price          NUMERIC,
    units_in_stock      INTEGER,
    units_on_order      INTEGER,
    reorder_level       INTEGER,
    discontinued        INTEGER,
    stock_alarm_level   INTEGER NOT NULL DEFAULT 0,
    attribute_signature TEXT NOT NULL,
    vigente_desde       TIMESTAMP NOT NULL,
    vigente_hasta       TIMESTAMP,
    es_vigente          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE dwa_enr_customer_sales_metrics (
    customer_key         INTEGER PRIMARY KEY,
    customer_id          TEXT NOT NULL,
    order_count          INTEGER NOT NULL,
    order_line_count     INTEGER NOT NULL,
    total_quantity       INTEGER NOT NULL,
    gross_amount         NUMERIC NOT NULL,
    discount_amount      NUMERIC NOT NULL,
    net_amount           NUMERIC NOT NULL,
    avg_order_net_amount NUMERIC,
    first_order_date     DATE,
    last_order_date      DATE,
    fecha_calculo        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_key) REFERENCES dwa_dim_customer(customer_key)
);

CREATE TABLE dwa_enr_product_sales_metrics (
    product_key         INTEGER PRIMARY KEY,
    product_id          INTEGER NOT NULL,
    order_count         INTEGER NOT NULL,
    order_line_count    INTEGER NOT NULL,
    total_quantity      INTEGER NOT NULL,
    gross_amount        NUMERIC NOT NULL,
    discount_amount     NUMERIC NOT NULL,
    net_amount          NUMERIC NOT NULL,
    avg_line_net_amount NUMERIC,
    first_order_date    DATE,
    last_order_date     DATE,
    fecha_calculo       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_key) REFERENCES dwa_dim_product(product_key)
);
