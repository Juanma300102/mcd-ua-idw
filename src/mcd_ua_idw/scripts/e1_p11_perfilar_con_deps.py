from sqlalchemy import text

NAME = "e1_p11_perfilar_con_deps"
VERSION = 1

_TABLAS_COLUMNAS: dict[str, list[str]] = {
    "txt_employees": [
        "employee_id", "last_name", "first_name", "title", "title_of_courtesy",
        "birth_date", "hire_date", "address", "city", "region", "postal_code", "country",
        "home_phone", "extension", "photo", "notes", "reports_to", "photo_path",
    ],
    "txt_products": [
        "product_id", "product_name", "supplier_id", "category_id", "quantity_per_unit",
        "unit_price", "units_in_stock", "units_on_order", "reorder_level", "discontinued",
    ],
    "txt_territories": ["territory_id", "territory_description", "region_id"],
    "txt_employee_territories": ["employee_id", "territory_id"],
    "txt_orders": [
        "order_id", "customer_id", "employee_id", "order_date", "required_date",
        "shipped_date", "ship_via", "freight", "ship_name", "ship_address", "ship_city",
        "ship_region", "ship_postal_code", "ship_country",
    ],
    "txt_order_details": ["order_id", "product_id", "unit_price", "quantity", "discount"],
}

_INSERT_PERFIL = text(
    "INSERT INTO dqm_perfilado "
    "(tabla, columna, nombre_script, total_filas, nulos, valores_distintos, "
    "valor_minimo, valor_maximo, outliers_detectados) "
    "VALUES (:tabla, :columna, :nombre_script, :total, :nulos, :distintos, "
    ":val_min, :val_max, :outliers)"
)


async def run(session):
    insertados = 0

    for tabla, columnas in _TABLAS_COLUMNAS.items():
        total_row = (await session.execute(
            text(f"SELECT COUNT(*) AS total FROM {tabla}")
        )).one()
        total = total_row.total

        for col in columnas:
            row = (await session.execute(text(
                f"SELECT "
                f"COUNT(*) - COUNT({col}) AS nulos, "
                f"COUNT(DISTINCT {col}) AS distintos, "
                f"MIN({col}) AS val_min, "
                f"MAX({col}) AS val_max "
                f"FROM {tabla}"
            ))).one()

            await session.execute(_INSERT_PERFIL, {
                "tabla": tabla,
                "columna": col,
                "nombre_script": NAME,
                "total": total,
                "nulos": row.nulos,
                "distintos": row.distintos,
                "val_min": str(row.val_min) if row.val_min is not None else None,
                "val_max": str(row.val_max) if row.val_max is not None else None,
                "outliers": 0,
            })
            insertados += 1

    return {"perfiles_insertados": insertados}
