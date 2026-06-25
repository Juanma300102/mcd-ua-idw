from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e1_p06_cargar_tmp_sin_deps"
VERSION = 1

_TABLAS_TXT = [
    "txt_categories",
    "txt_suppliers",
    "txt_shippers",
    "txt_regions",
    "txt_customers",
]

# (txt_tabla, tmp_tabla, insert_sql)
_CARGAS = [
    (
        "txt_categories",
        "tmp_categories",
        text(
            "INSERT INTO tmp_categories (category_id, category_name, description) "
            "SELECT CAST(category_id AS INTEGER), category_name, description "
            "FROM txt_categories"
        ),
    ),
    (
        "txt_suppliers",
        "tmp_suppliers",
        text(
            "INSERT INTO tmp_suppliers "
            "(supplier_id, company_name, contact_name, contact_title, address, city, "
            "region, postal_code, country, phone, fax, home_page) "
            "SELECT CAST(supplier_id AS INTEGER), company_name, contact_name, contact_title, "
            "address, city, region, postal_code, country, phone, fax, home_page "
            "FROM txt_suppliers"
        ),
    ),
    (
        "txt_shippers",
        "tmp_shippers",
        text(
            "INSERT INTO tmp_shippers (shipper_id, company_name, phone) "
            "SELECT CAST(shipper_id AS INTEGER), company_name, phone "
            "FROM txt_shippers"
        ),
    ),
    (
        "txt_regions",
        "tmp_regions",
        text(
            "INSERT INTO tmp_regions (region_id, region_description) "
            "SELECT CAST(region_id AS INTEGER), region_description "
            "FROM txt_regions"
        ),
    ),
    (
        "txt_customers",
        "tmp_customers",
        text(
            "INSERT INTO tmp_customers "
            "(customer_id, company_name, contact_name, contact_title, address, city, "
            "region, postal_code, country, phone, fax) "
            "SELECT customer_id, company_name, contact_name, contact_title, address, city, "
            "region, postal_code, country, phone, fax "
            "FROM txt_customers"
        ),
    ),
]

_INSERT_EVENTO = text(
    "INSERT INTO dqm_eventos "
    "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
    "registros_procesados, estado) "
    "VALUES (:tabla, :tipo_evento, :nombre_script, :fecha_inicio, :fecha_fin, "
    ":registros_procesados, :estado)"
)


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _check_validaciones(session) -> None:
    rows = (await session.execute(text(
        "SELECT tabla, columna, tipo_chequeo, detalle "
        "FROM dqm_validaciones "
        "WHERE resultado = 'ERROR' AND tabla = ANY(:tablas)"
    ), {"tablas": _TABLAS_TXT})).fetchall()

    if rows:
        detalle = "; ".join(f"{r.tabla}.{r.columna} [{r.tipo_chequeo}]: {r.detalle}" for r in rows)
        raise RuntimeError(
            f"Hay {len(rows)} validacion(es) con ERROR en dqm_validaciones. "
            f"Corregir antes de cargar TMP_. Detalle: {detalle}"
        )


async def _check_idempotencia(session) -> None:
    for _, tmp_tabla, _ in _CARGAS:
        count = (await session.execute(
            text(f"SELECT COUNT(*) FROM {tmp_tabla}")
        )).scalar()
        if count > 0:
            raise RuntimeError(
                f"{tmp_tabla} ya tiene {count} fila(s). "
                "Truncar las tablas TMP_ manualmente antes de volver a cargar."
            )


async def run(session):
    await _check_validaciones(session)
    await _check_idempotencia(session)

    filas_cargadas = {}

    for txt_tabla, tmp_tabla, insert_sql in _CARGAS:
        inicio = _now()
        result = await session.execute(insert_sql)
        fin = _now()

        filas = result.rowcount
        filas_cargadas[tmp_tabla] = filas

        await session.execute(_INSERT_EVENTO, {
            "tabla": tmp_tabla,
            "tipo_evento": "CARGA_TMP",
            "nombre_script": NAME,
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "registros_procesados": filas,
            "estado": "OK",
        })

    return {"filas_cargadas": filas_cargadas}
