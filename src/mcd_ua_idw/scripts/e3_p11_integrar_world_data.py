import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from mcd_ua_idw.script_runner.sql_utils import run_sql_file

NAME = "e3_p11_integrar_world_data"
VERSION = 1

_DATA_DIR = Path(__file__).parents[3] / "data" / "ingesta2"

# Mapeo de nombres de pais en Ingesta1/DWA → nombres en world-data-2023.csv
# (D2 de decisiones de diseno Etapa 3)
_PAIS_MAP = {
    "MX": "Mexico",
    "UK": "United Kingdom",
    "USA": "United States",
    "Ireland": "Republic of Ireland",
}

_ISO_FALLBACK = {
    # world-data-2023 trae Abbreviation vacio para Republic of Ireland.
    # Para tablero/mapas se registra el ISO-2 manual documentado.
    "Ireland": "IE",
}


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _leer_world_data() -> dict[str, dict]:
    """Carga world-data-2023.csv y devuelve dict country_name → atributos."""
    path = _DATA_DIR / "world-data-2023.csv"
    paises = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paises[row["Country"]] = {
                "iso_code": row.get("Abbreviation", "").strip(),
                "capital": row.get("Capital/Major City", "").strip(),
                "language": row.get("Official language", "").strip(),
                "currency": row.get("Currency-Code", "").strip(),
                "latitude": row.get("Latitude", "").strip(),
                "longitude": row.get("Longitude", "").strip(),
            }
    return paises


async def run(session):
    # 1. DDL: crear txt_world_data y agregar columnas a dwa_dim_geography
    sql_path = Path(__file__).parent / "e3_p11_integrar_world_data.sql"
    await run_sql_file(session, sql_path)

    # 2. Cargar world-data-2023.csv en txt_world_data
    t0 = _now()
    world = _leer_world_data()
    rows_txt = [
        {
            "country": name,
            "iso_code": attrs["iso_code"],
            "capital": attrs["capital"],
            "official_language": attrs["language"],
            "currency_code": attrs["currency"],
            "latitude": attrs["latitude"] or None,
            "longitude": attrs["longitude"] or None,
        }
        for name, attrs in world.items()
    ]
    await session.execute(
        text(
            "INSERT INTO txt_world_data "
            "(country, iso_code, capital, official_language, currency_code, latitude, longitude) "
            "VALUES (:country, :iso_code, :capital, :official_language, :currency_code, :latitude, :longitude)"
        ),
        rows_txt,
    )

    # 3. UPDATE dwa_dim_geography con los atributos, aplicando mapeo de nombres
    actualizados = 0
    for dwa_country, world_country in [
        *[(c, c) for c in world if c not in _PAIS_MAP.values()],
        *_PAIS_MAP.items(),
    ]:
        attrs = world.get(world_country)
        if not attrs:
            continue

        lat = float(attrs["latitude"]) if attrs["latitude"] else None
        lon = float(attrs["longitude"]) if attrs["longitude"] else None

        result = await session.execute(
            text(
                "UPDATE dwa_dim_geography SET "
                "country_iso_code = :iso, country_capital = :capital, "
                "country_language = :lang, country_currency = :curr, "
                "country_latitude = :lat, country_longitude = :lon "
                "WHERE country = :dwa_country"
            ),
            {
                "iso": attrs["iso_code"] or _ISO_FALLBACK.get(dwa_country),
                "capital": attrs["capital"] or None,
                "lang": attrs["language"] or None,
                "curr": attrs["currency"] or None,
                "lat": lat,
                "lon": lon,
                "dwa_country": dwa_country,
            },
        )
        actualizados += result.rowcount

    # 4. Registrar evento DQM
    await session.execute(
        text(
            "INSERT INTO dqm_eventos "
            "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
            "registros_procesados, estado, observaciones) "
            "VALUES ('dwa_dim_geography', 'ENRIQUECIMIENTO', :n, :fi, :ff, :rp, 'OK', :obs)"
        ),
        {
            "n": NAME,
            "fi": t0,
            "ff": _now(),
            "rp": actualizados,
            "obs": f"world-data-2023: {len(world)} paises en txt_world_data; {actualizados} filas de dwa_dim_geography enriquecidas",
        },
    )

    # 5. Registrar entidad en MET_
    exists = (
        await session.execute(
            text("SELECT 1 FROM met_entidades WHERE nombre = 'txt_world_data'")
        )
    ).fetchone()
    if not exists:
        await session.execute(
            text(
                "INSERT INTO met_entidades (nombre, capa, tipo_entidad, descripcion, fuente, activa) "
                "VALUES ('txt_world_data', 'TXT_NOV', 'TABLA', "
                "'Datos de paises world-data-2023 en raw TEXT', 'world-data-2023.csv', 1)"
            )
        )

    return {
        "paises_en_world_data": len(world),
        "filas_geography_enriquecidas": actualizados,
    }
