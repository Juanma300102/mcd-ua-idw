from sqlalchemy import text

NAME = "e1_p05_perfilar_sin_deps"
VERSION = 1

_TABLAS_COLUMNAS: dict[str, list[str]] = {
    "txt_categories": ["category_id", "category_name", "description", "picture"],
    "txt_suppliers": [
        "supplier_id", "company_name", "contact_name", "contact_title",
        "address", "city", "region", "postal_code", "country", "phone", "fax", "home_page",
    ],
    "txt_shippers": ["shipper_id", "company_name", "phone"],
    "txt_regions": ["region_id", "region_description"],
    "txt_customers": [
        "customer_id", "company_name", "contact_name", "contact_title",
        "address", "city", "region", "postal_code", "country", "phone", "fax",
    ],
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
