from sqlalchemy import text

NAME = "e2_p06_perfilar_dwa"
VERSION = 1

_TABLAS_COLUMNAS: dict[str, list[str]] = {
    "dwa_dim_date": [
        "date_key",
        "full_date",
        "year_number",
        "quarter_number",
        "month_number",
        "day_number",
    ],
    "dwa_dim_geography": [
        "geography_key",
        "geography_signature",
        "country",
        "region",
        "city",
        "postal_code",
        "fecha_carga",
    ],
    "dwa_dim_customer": [
        "customer_key",
        "customer_id",
        "customer_geography_key",
        "company_name",
        "contact_name",
        "contact_title",
        "city",
        "region",
        "postal_code",
        "country",
        "phone",
        "fax",
        "fecha_carga",
    ],
    "dwa_dim_product": [
        "product_key",
        "product_id",
        "product_name",
        "category_id",
        "category_name",
        "supplier_id",
        "supplier_name",
        "quantity_per_unit",
        "unit_price",
        "units_in_stock",
        "units_on_order",
        "reorder_level",
        "discontinued",
        "stock_alarm_level",
        "fecha_carga",
    ],
    "dwa_dim_employee": [
        "employee_key",
        "employee_id",
        "employee_geography_key",
        "employee_name",
        "title",
        "city",
        "region",
        "country",
        "reports_to",
        "fecha_carga",
    ],
    "dwa_dim_shipper": [
        "shipper_key",
        "shipper_id",
        "company_name",
        "phone",
        "fecha_carga",
    ],
    "dwa_fact_order_lines": [
        "order_line_key",
        "order_id",
        "product_id",
        "customer_key",
        "product_key",
        "employee_key",
        "shipper_key",
        "ship_geography_key",
        "order_date_key",
        "required_date_key",
        "shipped_date_key",
        "unit_price",
        "quantity",
        "discount",
        "gross_amount",
        "discount_amount",
        "net_amount",
        "order_freight_amount",
        "fecha_carga",
    ],
    "dwm_customer_history": [
        "customer_history_key",
        "customer_id",
        "company_name",
        "contact_name",
        "contact_title",
        "city",
        "region",
        "postal_code",
        "country",
        "phone",
        "fax",
        "attribute_signature",
        "vigente_desde",
        "vigente_hasta",
        "es_vigente",
    ],
    "dwm_product_history": [
        "product_history_key",
        "product_id",
        "product_name",
        "category_id",
        "category_name",
        "supplier_id",
        "supplier_name",
        "quantity_per_unit",
        "unit_price",
        "units_in_stock",
        "units_on_order",
        "reorder_level",
        "discontinued",
        "stock_alarm_level",
        "attribute_signature",
        "vigente_desde",
        "vigente_hasta",
        "es_vigente",
    ],
    "dwa_enr_customer_sales_metrics": [
        "customer_key",
        "customer_id",
        "order_count",
        "order_line_count",
        "total_quantity",
        "gross_amount",
        "discount_amount",
        "net_amount",
        "avg_order_net_amount",
        "first_order_date",
        "last_order_date",
        "fecha_calculo",
    ],
    "dwa_enr_product_sales_metrics": [
        "product_key",
        "product_id",
        "order_count",
        "order_line_count",
        "total_quantity",
        "gross_amount",
        "discount_amount",
        "net_amount",
        "avg_line_net_amount",
        "first_order_date",
        "last_order_date",
        "fecha_calculo",
    ],
}

_INSERT_PERFIL = text(
    "INSERT INTO dqm_perfilado "
    "(tabla, columna, nombre_script, total_filas, nulos, valores_distintos, "
    "valor_minimo, valor_maximo, outliers_detectados, observaciones) "
    "VALUES (:tabla, :columna, :nombre_script, :total, :nulos, :distintos, "
    ":val_min, :val_max, :outliers, :observaciones)"
)


async def _insert_table_profile(session, *, tabla: str, total: int) -> None:
    await session.execute(
        _INSERT_PERFIL,
        {
            "tabla": tabla,
            "columna": None,
            "nombre_script": NAME,
            "total": total,
            "nulos": None,
            "distintos": None,
            "val_min": None,
            "val_max": None,
            "outliers": 0,
            "observaciones": "Perfil de tabla DWA: total de filas cargadas.",
        },
    )


async def run(session):
    insertados = 0

    for tabla, columnas in _TABLAS_COLUMNAS.items():
        total = (
            await session.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
        ).scalar_one()
        await _insert_table_profile(session, tabla=tabla, total=total)
        insertados += 1

        for col in columnas:
            row = (
                await session.execute(
                    text(
                        f"SELECT "
                        f"COUNT(*) - COUNT({col}) AS nulos, "
                        f"COUNT(DISTINCT {col}) AS distintos, "
                        f"MIN({col}) AS val_min, "
                        f"MAX({col}) AS val_max "
                        f"FROM {tabla}"
                    )
                )
            ).one()

            await session.execute(
                _INSERT_PERFIL,
                {
                    "tabla": tabla,
                    "columna": col,
                    "nombre_script": NAME,
                    "total": total,
                    "nulos": row.nulos,
                    "distintos": row.distintos,
                    "val_min": str(row.val_min) if row.val_min is not None else None,
                    "val_max": str(row.val_max) if row.val_max is not None else None,
                    "outliers": 0,
                    "observaciones": "Perfil DWA posterior a carga inicial.",
                },
            )
            insertados += 1

    return {"perfiles_insertados": insertados}
