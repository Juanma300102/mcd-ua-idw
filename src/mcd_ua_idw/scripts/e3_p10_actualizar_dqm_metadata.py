from datetime import UTC, datetime

from sqlalchemy import text

NAME = "e3_p10_actualizar_dqm_metadata"
VERSION = 1

_NUEVOS_PROCESOS = [
    ("e3_p01_crear_tablas_txt_ingesta2", "3", "01", "DDL",      "TXT_NOV", "TXT_NOV", "Crea TXT_ para novedades Ingesta2", 21, 0),
    ("e3_p02_crear_tablas_tmp_ingesta2", "3", "02", "DDL",      "TMP_NOV", "TMP_NOV", "Crea TMP_ para novedades Ingesta2", 22, 0),
    ("e3_p03_cargar_txt_ingesta2",       "3", "03", "CARGA",    "CSV",     "TXT_NOV", "Carga CSVs Ingesta2 a TXT_",         23, 0),
    ("e3_p04_validar_tipos_ingesta2",    "3", "04", "DQM",      "TXT_NOV", "DQM",     "Valida formato y PK en TXT_NOV",    24, 1),
    ("e3_p05_perfilar_ingesta2",         "3", "05", "DQM",      "TXT_NOV", "DQM",     "Perfilado descriptivo TXT_NOV",     25, 0),
    ("e3_p06_cargar_tmp_ingesta2",       "3", "06", "CARGA",    "TXT_NOV", "TMP_NOV", "Carga TXT_ a TMP_ con validacion",  26, 1),
    ("e3_p07_validar_integridad_ingesta2","3","07", "DQM",      "TMP_NOV", "DQM",     "Chequeos FK TMP_NOV vs TMP_",       27, 1),
    ("e3_p08_actualizar_dwa",            "3", "08", "SCD2",     "TMP_NOV", "DWA_DWM", "SCD2 customers/products + fact nuevas", 28, 1),
    ("e3_p09_actualizar_enriquecimiento","3", "09", "ENRIQUECIMIENTO", "DWA", "DWA",  "Recalculo metricas enriquecimiento", 29, 0),
    ("e3_p10_actualizar_dqm_metadata",   "3", "10", "METADATA", "DWA",    "MET",     "Actualiza MET_ post-Etapa3",         30, 0),
    ("e3_p11_integrar_world_data",       "3", "11", "ENRIQUECIMIENTO", "CSV", "DWA",  "Integra world-data-2023 en geografia", 31, 0),
    ("e3_p12_integrar_customer_score",   "3", "12", "ENRIQUECIMIENTO", "CSV", "DWA",  "Integra customer_score",             32, 0),
]

_NUEVAS_ENTIDADES = [
    ("txt_customers_nov",     "TXT_NOV", "TABLA", "Novedades de clientes Ingesta2 — raw TEXT", None, None),
    ("txt_products_nov",      "TXT_NOV", "TABLA", "Novedades de productos Ingesta2 — raw TEXT", None, None),
    ("txt_orders_nov",        "TXT_NOV", "TABLA", "Novedades de ordenes Ingesta2 — raw TEXT", None, None),
    ("txt_order_details_nov", "TXT_NOV", "TABLA", "Novedades de detalles de orden Ingesta2 — raw TEXT", None, None),
    ("tmp_customers_nov",     "TMP_NOV", "TABLA", "Novedades de clientes con tipos del DER", None, None),
    ("tmp_products_nov",      "TMP_NOV", "TABLA", "Novedades de productos con tipos del DER", None, None),
    ("tmp_orders_nov",        "TMP_NOV", "TABLA", "Novedades de ordenes con tipos del DER", None, None),
    ("tmp_order_details_nov", "TMP_NOV", "TABLA", "Novedades de detalles de orden con tipos del DER", None, None),
    ("dwa_enr_customer_score","DWA",     "ENRIQUECIMIENTO", "Score externo de clientes (TP-11)", "1 fila por cliente con score", "customers_score.csv"),
]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def run(session):
    t0 = _now()
    insertados_procesos = 0
    insertados_entidades = 0

    # Registrar procesos Etapa 3 en met_procesos (si no existen ya)
    for (nombre, etapa, paso, tipo, capa_origen, capa_destino,
         descripcion, orden, requiere_val) in _NUEVOS_PROCESOS:
        exists = (await session.execute(text(
            "SELECT 1 FROM met_procesos WHERE nombre_script = :n"
        ), {"n": nombre})).fetchone()
        if not exists:
            await session.execute(text(
                "INSERT INTO met_procesos "
                "(nombre_script, etapa, paso, tipo_proceso, capa_origen, capa_destino, "
                "descripcion, orden_ejecucion, requiere_validacion) "
                "VALUES (:n, :et, :pa, :tp, :co, :cd, :desc, :ord, :rv)"
            ), {
                "n": nombre, "et": etapa, "pa": paso, "tp": tipo,
                "co": capa_origen, "cd": capa_destino, "desc": descripcion,
                "ord": orden, "rv": requiere_val,
            })
            insertados_procesos += 1

    # Registrar entidades nuevas en met_entidades (si no existen ya)
    for (nombre, capa, tipo, descripcion, grano, fuente) in _NUEVAS_ENTIDADES:
        exists = (await session.execute(text(
            "SELECT 1 FROM met_entidades WHERE nombre = :n"
        ), {"n": nombre})).fetchone()
        if not exists:
            await session.execute(text(
                "INSERT INTO met_entidades "
                "(nombre, capa, tipo_entidad, descripcion, grano, fuente, activa) "
                "VALUES (:n, :c, :te, :d, :g, :f, 1)"
            ), {
                "n": nombre, "c": capa, "te": tipo,
                "d": descripcion, "g": grano, "f": fuente,
            })
            insertados_entidades += 1

    await session.execute(text(
        "INSERT INTO dqm_eventos "
        "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
        "registros_procesados, estado, observaciones) "
        "VALUES ('met_procesos', 'ACTUALIZACION_METADATA', :n, :fi, :ff, :rp, 'OK', :obs)"
    ), {
        "n": NAME,
        "fi": t0,
        "ff": _now(),
        "rp": insertados_procesos + insertados_entidades,
        "obs": f"Etapa 3: {insertados_procesos} procesos y {insertados_entidades} entidades registradas en MET_",
    })

    return {
        "procesos_registrados": insertados_procesos,
        "entidades_registradas": insertados_entidades,
    }
