import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e3_p12_integrar_customer_score"
VERSION = 1

_DATA_DIR = Path(__file__).parents[3] / "data" / "ingesta2"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def run(session):
    # 1. DDL: crear txt_customer_score y dwa_enr_customer_score
    sql_path = Path(__file__).parent / "e3_p12_integrar_customer_score.sql"
    await run_sql_file(session, sql_path)

    t0 = _now()

    # 2. Cargar customers_score.csv (separador ;) en txt_customer_score
    path = _DATA_DIR / "customers_score.csv"
    rows_txt = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f, delimiter=";"):
            rows_txt.append({
                "customer_id": raw.get("customerID", "").strip(),
                "score": raw.get("score", "").strip(),
            })

    await session.execute(
        text("INSERT INTO txt_customer_score (customer_id, score) VALUES (:customer_id, :score)"),
        rows_txt,
    )

    # 3. Cargar dwa_enr_customer_score desde txt_customer_score
    #    Solo clientes que existen en dwa_dim_customer (83 de 91)
    result = await session.execute(text(
        "WITH deduped AS ("
        "  SELECT DISTINCT ON (ts.customer_id) "
        "    c.customer_key, c.customer_id, CAST(ts.score AS INTEGER) AS score "
        "  FROM txt_customer_score ts "
        "  JOIN dwa_dim_customer c ON ts.customer_id = c.customer_id "
        "  WHERE ts.score IS NOT NULL AND ts.score != '' "
        "  ORDER BY ts.customer_id, CAST(ts.score AS INTEGER) DESC"
        ") "
        "INSERT INTO dwa_enr_customer_score (customer_key, customer_id, score) "
        "SELECT customer_key, customer_id, score FROM deduped "
        "ON CONFLICT (customer_id) DO UPDATE SET score = EXCLUDED.score, "
        "fecha_carga = CURRENT_TIMESTAMP"
    ))
    n_scores = result.rowcount

    # 4. Registrar evento DQM
    await session.execute(text(
        "INSERT INTO dqm_eventos "
        "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
        "registros_procesados, estado, observaciones) "
        "VALUES ('dwa_enr_customer_score', 'ENRIQUECIMIENTO', :n, :fi, :ff, :rp, 'OK', :obs)"
    ), {
        "n": NAME,
        "fi": t0,
        "ff": _now(),
        "rp": n_scores,
        "obs": f"customer_score: {len(rows_txt)} filas en staging; {n_scores} scores en dwa_enr_customer_score",
    })

    # 5. Registrar entidades en MET_
    for nombre, capa, tipo_ent, desc in [
        ("txt_customer_score",    "TXT_NOV", "TABLA",          "Score de clientes Ingesta2 — raw TEXT"),
        ("dwa_enr_customer_score","DWA",     "ENRIQUECIMIENTO", "Score externo de clientes (TP-11). 1 fila por cliente con score."),
    ]:
        exists = (await session.execute(text(
            "SELECT 1 FROM met_entidades WHERE nombre = :n"
        ), {"n": nombre})).fetchone()
        if not exists:
            await session.execute(text(
                "INSERT INTO met_entidades (nombre, capa, tipo_entidad, descripcion, fuente, activa) "
                "VALUES (:n, :c, :te, :d, 'customers_score.csv', 1)"
            ), {"n": nombre, "c": capa, "te": tipo_ent, "d": desc})

    return {
        "filas_staging": len(rows_txt),
        "scores_cargados": n_scores,
    }
