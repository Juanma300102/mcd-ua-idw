from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Any

from sqlalchemy import text

NAME = "e4_p05_generar_tableros_html"
VERSION = 1

_ROOT = Path(__file__).parents[3]
_OUT_DIR = _ROOT / "DOCS" / "etapa4"


def _serialize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:,.2f}"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _currency(value: Any) -> str:
    if value is None:
        return "$0.00"
    amount = Decimal(value)
    return f"${amount:,.2f}"


def _table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body = []
    for row in rows:
        cells = "".join(
            f"<td>{escape(_serialize(row.get(key)))}</td>" for key, _ in columns
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def _bar_list(rows: list[dict[str, Any]], label_key: str, value_key: str) -> str:
    if not rows:
        return "<p>Sin datos.</p>"
    max_value = max(Decimal(row[value_key] or 0) for row in rows) or Decimal(1)
    items = []
    for row in rows:
        value = Decimal(row[value_key] or 0)
        width = max(2, int((value / max_value) * 100))
        items.append(
            '<div class="bar-row">'
            f"<span>{escape(_serialize(row[label_key]))}</span>"
            f'<div class="bar"><i style="width:{width}%"></i></div>'
            f"<strong>{escape(_currency(value))}</strong>"
            "</div>"
        )
    return "".join(items)


def _line_chart(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>Sin datos.</p>"

    width = 920
    height = 320
    padding_left = 72
    padding_right = 28
    padding_top = 24
    padding_bottom = 54
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom

    values = [Decimal(row["venta_neta"] or 0) for row in rows]
    max_value = max(values) or Decimal(1)
    x_step = plot_width / max(len(rows) - 1, 1)

    points = []
    circles = []
    labels = []
    label_every = max(1, len(rows) // 6)
    for index, row in enumerate(rows):
        value = Decimal(row["venta_neta"] or 0)
        x = padding_left + (x_step * index)
        y = padding_top + plot_height - (float(value / max_value) * plot_height)
        points.append(f"{x:.2f},{y:.2f}")
        tooltip = (
            f"{row['periodo']}: {_currency(value)} de venta neta; "
            f"{_serialize(row['ordenes'])} ordenes"
        )
        circles.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5">'
            f"<title>{escape(tooltip)}</title>"
            "</circle>"
        )
        if index == 0 or index == len(rows) - 1 or index % label_every == 0:
            labels.append(
                f'<text x="{x:.2f}" y="{height - 18}" text-anchor="middle">'
                f"{escape(_serialize(row['periodo']))}</text>"
            )

    y_axis_label = escape(_currency(max_value))
    return (
        '<div class="chart-card">'
        f'<svg class="line-chart" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Evolucion mensual de venta neta">'
        f'<line class="axis" x1="{padding_left}" y1="{height - padding_bottom}" '
        f'x2="{width - padding_right}" y2="{height - padding_bottom}" />'
        f'<line class="axis" x1="{padding_left}" y1="{padding_top}" '
        f'x2="{padding_left}" y2="{height - padding_bottom}" />'
        f'<text x="{padding_left - 10}" y="{padding_top + 6}" text-anchor="end">{y_axis_label}</text>'
        f'<text x="{padding_left - 10}" y="{height - padding_bottom}" text-anchor="end">$0</text>'
        f'<polyline points="{" ".join(points)}" />'
        f'{"".join(circles)}'
        f'{"".join(labels)}'
        "</svg>"
        '<p class="chart-note">Cada punto muestra la venta neta mensual; pasar el mouse por un punto muestra también la cantidad de órdenes.</p>'
        "</div>"
    )


def _html(title: str, subtitle: str, body: str) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; margin: 32px; color: #162033; background: #f7f9fc; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; color: #163b73; }}
    h2 {{ margin-top: 28px; color: #163b73; }}
    .subtitle {{ color: #52627a; margin: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }}
    .card {{ background: white; border: 1px solid #dce5f2; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(22,32,51,.06); }}
    .metric {{ font-size: 26px; font-weight: 700; color: #0f766e; }}
    table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 12px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #e7edf5; padding: 10px 12px; text-align: left; }}
    th {{ background: #eaf1fb; color: #163b73; font-size: 13px; }}
    .bar-row {{ display: grid; grid-template-columns: 180px 1fr 140px; gap: 12px; align-items: center; margin: 10px 0; }}
    .bar {{ background: #e5eaf3; height: 16px; border-radius: 999px; overflow: hidden; }}
    .bar i {{ display: block; height: 100%; background: linear-gradient(90deg, #2563eb, #0f766e); }}
    .chart-card {{ background: white; border: 1px solid #dce5f2; border-radius: 12px; padding: 16px; }}
    .line-chart {{ width: 100%; height: auto; }}
    .line-chart .axis {{ stroke: #90a4c3; stroke-width: 1; }}
    .line-chart polyline {{ fill: none; stroke: #2563eb; stroke-width: 3; }}
    .line-chart circle {{ fill: #0f766e; stroke: white; stroke-width: 2; cursor: help; }}
    .line-chart text {{ fill: #52627a; font-size: 12px; }}
    .chart-note {{ color: #52627a; font-size: 13px; margin: 8px 0 0; }}
    footer {{ margin-top: 32px; color: #52627a; font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <p class="subtitle">{escape(subtitle)}</p>
  </header>
  {body}
  <footer>Generado por {NAME} — {generated_at}</footer>
</body>
</html>
"""


async def _rows(session, sql: str) -> list[dict[str, Any]]:
    result = await session.execute(text(sql))
    return [dict(row) for row in result.mappings().all()]


async def _write_business_dashboard(session) -> Path:
    kpis = (
        await _rows(
            session,
            """
        SELECT
          COUNT(*) AS filas_dp,
          COUNT(DISTINCT ship_country) AS paises,
          SUM(ordenes) AS ordenes,
          SUM(lineas_orden) AS lineas,
          SUM(net_amount) AS venta_neta
        FROM dp01_ventas_geo_score
    """,
        )
    )[0]
    top_countries = await _rows(
        session,
        """
        SELECT ship_country, country_iso_code, SUM(ordenes) AS ordenes, SUM(net_amount) AS venta_neta
        FROM dp01_ventas_geo_score
        GROUP BY ship_country, country_iso_code
        ORDER BY SUM(net_amount) DESC
        LIMIT 10
    """,
    )
    score_segments = await _rows(
        session,
        """
        SELECT score_segment,
               CASE score_segment
                 WHEN 'alto_4_5' THEN 'Alto (4-5)'
                 WHEN 'medio_2_3' THEN 'Medio (2-3)'
                 WHEN 'bajo_0_1' THEN 'Bajo (0-1)'
                 WHEN 'sin_score' THEN 'Sin score'
                 ELSE score_segment
               END AS score_segment_label,
               MIN(score_segment_order) AS orden, SUM(ordenes) AS ordenes,
               SUM(net_amount) AS venta_neta
        FROM dp01_ventas_geo_score
        GROUP BY score_segment
        ORDER BY MIN(score_segment_order)
    """,
    )
    monthly = await _rows(
        session,
        """
        SELECT periodo, SUM(ordenes) AS ordenes, SUM(net_amount) AS venta_neta
        FROM dp01_ventas_geo_score
        GROUP BY periodo
        ORDER BY periodo
    """,
    )

    body = f"""
<section class="grid">
  <div class="card"><div class="metric">{_serialize(kpis['filas_dp'])}</div><div>filas DP</div></div>
  <div class="card"><div class="metric">{_serialize(kpis['paises'])}</div><div>países</div></div>
  <div class="card"><div class="metric">{_serialize(kpis['ordenes'])}</div><div>órdenes</div></div>
  <div class="card"><div class="metric">{_currency(kpis['venta_neta'])}</div><div>venta neta</div></div>
</section>
<h2>Top países por venta neta</h2>
{_bar_list(top_countries, 'ship_country', 'venta_neta')}
<h2>Segmentos de score</h2>
{_table(score_segments, [('score_segment_label', 'Segmento'), ('ordenes', 'Órdenes'), ('venta_neta', 'Venta neta')])}
<h2>Evolución mensual</h2>
{_line_chart(monthly)}
"""
    path = _OUT_DIR / "tablero_dp01_ventas_geo_score.html"
    path.write_text(
        _html(
            "DP01 — Ventas por geografía y score",
            "Producto de datos publicado desde DWA, world-data-2023 y customer_score.",
            body,
        ),
        encoding="utf-8",
    )
    return path


async def _write_dqm_dashboard(session) -> Path:
    validation_status = await _rows(
        session,
        """
        SELECT resultado, SUM(checks) AS checks, SUM(registros_afectados_total) AS afectados
        FROM dp02_dqm_validaciones_resumen
        GROUP BY resultado
        ORDER BY resultado
    """,
    )
    event_status = await _rows(
        session,
        """
        SELECT estado, SUM(eventos) AS eventos, SUM(registros_procesados_total) AS procesados
        FROM dp02_dqm_eventos_resumen
        GROUP BY estado
        ORDER BY estado
    """,
    )
    top_profiles = await _rows(
        session,
        """
        SELECT tabla, columnas_perfiladas, total_filas_maximo, nulos_total, outliers_total
        FROM dp02_dqm_perfilado_resumen
        ORDER BY total_filas_maximo DESC NULLS LAST, tabla
        LIMIT 15
    """,
    )
    recent_validations = await _rows(
        session,
        """
        SELECT nombre_script, tabla, tipo_chequeo, resultado, registros_afectados_total, ultima_fecha
        FROM dp02_dqm_validaciones_resumen
        ORDER BY ultima_fecha DESC NULLS LAST
        LIMIT 15
    """,
    )

    body = f"""
<h2>Estado de validaciones</h2>
{_table(validation_status, [('resultado', 'Resultado'), ('checks', 'Checks'), ('afectados', 'Registros afectados')])}
<h2>Eventos de proceso</h2>
{_table(event_status, [('estado', 'Estado'), ('eventos', 'Eventos'), ('procesados', 'Registros procesados')])}
<h2>Tablas con mayor volumen perfilado</h2>
{_table(top_profiles, [('tabla', 'Tabla'), ('columnas_perfiladas', 'Columnas'), ('total_filas_maximo', 'Filas máx.'), ('nulos_total', 'Nulos'), ('outliers_total', 'Outliers')])}
<h2>Validaciones recientes</h2>
{_table(recent_validations, [('nombre_script', 'Script'), ('tabla', 'Tabla'), ('tipo_chequeo', 'Chequeo'), ('resultado', 'Resultado'), ('registros_afectados_total', 'Afectados'), ('ultima_fecha', 'Última fecha')])}
"""
    path = _OUT_DIR / "tablero_dp02_dqm.html"
    path.write_text(
        _html(
            "DP02 — Tablero de calidad DQM",
            "Vista navegable de validaciones, eventos y perfilado persistidos en DQM.",
            body,
        ),
        encoding="utf-8",
    )
    return path


async def run(session):
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    business_path = await _write_business_dashboard(session)
    dqm_path = await _write_dqm_dashboard(session)

    await session.execute(
        text(
            "INSERT INTO dqm_eventos "
            "(tabla, tipo_evento, nombre_script, fecha_inicio, fecha_fin, "
            "registros_procesados, estado, observaciones) "
            "VALUES ('DOCS/etapa4', 'GENERACION_TABLERO', :n, CURRENT_TIMESTAMP, "
            "CURRENT_TIMESTAMP, 2, 'OK', :obs)"
        ),
        {
            "n": NAME,
            "obs": f"Tableros HTML generados: {business_path.name}, {dqm_path.name}",
        },
    )

    return {
        "archivos_generados": [
            str(business_path.relative_to(_ROOT)),
            str(dqm_path.relative_to(_ROOT)),
        ]
    }
