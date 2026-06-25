import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

NAME = "e1_p09_cargar_txt_con_deps"
VERSION = 1

_DATA_DIR = Path(__file__).parents[3] / "data" / "ingesta1"

# (csv_file, delimiter, txt_table, {csv_col: sql_col, ...})
_TABLAS = [
    (
        "employees.csv",
        ",",
        "txt_employees",
        {
            "employeeID":       "employee_id",
            "lastName":         "last_name",
            "firstName":        "first_name",
            "title":            "title",
            "titleOfCourtesy":  "title_of_courtesy",
            "birthDate":        "birth_date",
            "hireDate":         "hire_date",
            "address":          "address",
            "city":             "city",
            "region":           "region",
            "postalCode":       "postal_code",
            "country":          "country",
            "homePhone":        "home_phone",
            "extension":        "extension",
            "photo":            "photo",
            "notes":            "notes",
            "reportsTo":        "reports_to",
            "photoPath":        "photo_path",
        },
    ),
    (
        "products.csv",
        ",",
        "txt_products",
        {
            "productID":       "product_id",
            "productName":     "product_name",
            "supplierID":      "supplier_id",
            "categoryID":      "category_id",
            "quantityPerUnit": "quantity_per_unit",
            "unitPrice":       "unit_price",
            "unitsInStock":    "units_in_stock",
            "unitsOnOrder":    "units_on_order",
            "reorderLevel":    "reorder_level",
            "discontinued":    "discontinued",
        },
    ),
    (
        "territories.csv",
        ",",
        "txt_territories",
        {
            "territoryid":          "territory_id",
            "territorydescription": "territory_description",
            "regionid":             "region_id",
        },
    ),
    (
        "employee_territories.csv",
        ",",
        "txt_employee_territories",
        {
            "employeeid":  "employee_id",
            "territoryid": "territory_id",
        },
    ),
    (
        "orders.csv",
        ",",
        "txt_orders",
        {
            "orderID":        "order_id",
            "customerID":     "customer_id",
            "employeeID":     "employee_id",
            "orderDate":      "order_date",
            "requiredDate":   "required_date",
            "shippedDate":    "shipped_date",
            "shipVia":        "ship_via",
            "freight":        "freight",
            "shipName":       "ship_name",
            "shipAddress":    "ship_address",
            "shipCity":       "ship_city",
            "shipRegion":     "ship_region",
            "shipPostalCode": "ship_postal_code",
            "shipCountry":    "ship_country",
        },
    ),
    (
        "order_details.csv",
        ",",
        "txt_order_details",
        {
            "orderID":    "order_id",
            "productID":  "product_id",
            "unitPrice":  "unit_price",
            "quantity":   "quantity",
            "discount":   "discount",
        },
    ),
]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _leer_csv(csv_file: str, delimiter: str, col_map: dict) -> list[dict]:
    path = _DATA_DIR / csv_file
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f, delimiter=delimiter):
            row = {}
            for csv_col, sql_col in col_map.items():
                val = raw.get(csv_col)
                row[sql_col] = None if val == "NULL" else val
            rows.append(row)
    return rows


async def run(session):
    filas_cargadas = {}

    for csv_file, delimiter, tabla, col_map in _TABLAS:
        inicio = _now()
        rows = _leer_csv(csv_file, delimiter, col_map)

        cols = list(col_map.values())
        placeholders = ", ".join(f":{c}" for c in cols)
        col_list = ", ".join(cols)
        insert_sql = text(f"INSERT INTO {tabla} ({col_list}) VALUES ({placeholders})")

        await session.execute(insert_sql, rows)

        fin = _now()
        filas_cargadas[tabla] = len(rows)

        await session.execute(
            text(
                "INSERT INTO dqm_eventos "
                "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
                "registros_procesados, estado) "
                "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
                ":registros_procesados, :estado)"
            ),
            {
                "tabla": tabla,
                "tipo_evento": "CARGA_TXT",
                "nombre_script": NAME,
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "registros_procesados": len(rows),
                "estado": "OK",
            },
        )

    return {"filas_cargadas": filas_cargadas}
