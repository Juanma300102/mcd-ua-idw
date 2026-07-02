# Etapa 4 — Publicación

Etapa 4 publica productos de datos `DPxx_` desde el DWA ya actualizado por
Ingesta2 y genera dos tableros HTML: uno de negocio y otro de navegación DQM.

## Quick path

1. Re-ejecutar manualmente `e3_p11_integrar_world_data` para aplicar el mapeo
   final de geografía (`MX → Mexico`, `Ireland → IE`).
2. Ejecutar manualmente `e4_p01_crear_tablas_publicacion`.
3. Ejecutar manualmente `e4_p02_cargar_productos_publicacion`.
4. Ejecutar manualmente `e4_p03_validar_productos_publicacion`.
5. Ejecutar manualmente `e4_p04_documentar_metadata_publicacion`.
6. Ejecutar manualmente `e4_p05_generar_tableros_html`.
7. Verificar los HTML en `DOCS/etapa4/`.

> Regla del proyecto: los scripts con `CREATE TABLE`/`DROP TABLE` se escriben
> en el repo pero los ejecuta manualmente una persona desde `uv run idw-scripts`.

## Productos publicados

| Producto | Grano | Uso |
|---|---|---|
| `dp01_ventas_geo_score` | mes + país de envío + segmento de score | Tablero comercial de ventas con geografía enriquecida y customer score |
| `dp02_dqm_validaciones_resumen` | script + tabla + columna + chequeo + resultado | Tablero DQM: validaciones |
| `dp02_dqm_eventos_resumen` | script + tabla + evento + estado | Tablero DQM: procesos ejecutados |
| `dp02_dqm_perfilado_resumen` | tabla perfilada | Tablero DQM: estadísticas descriptivas |

### DP01 — ventas por geografía y score

`dp01_ventas_geo_score` combina:

- `dwa_fact_order_lines`
- `dwa_dim_date`
- `dwa_dim_geography`
- `dwa_dim_customer`
- `dwa_enr_customer_score`

Segmentos de score:

| Segmento | Regla |
|---|---|
| `alto_4_5` | `score >= 4` |
| `medio_2_3` | `score >= 2 AND score < 4` |
| `bajo_0_1` | `score < 2` |
| `sin_score` | cliente sin score externo |

## Calidad y Metadata

Etapa 4 deja huella en:

- `dqm_eventos`: carga de productos y generación de tableros.
- `dqm_validaciones`: controles de publicación (`DP01_*`, `DP02_*`,
  `DQM_SIN_ERRORES_PREVIOS`).
- `MET_*`: procesos, entidades, atributos e indicadores de publicación.

Checklist de aceptación:

- [ ] `dp01_ventas_geo_score` tiene filas.
- [ ] DP01 contiene filas con score externo (`score_segment <> 'sin_score'`).
- [ ] DP01 no tiene geografía enriquecida incompleta.
- [ ] Las tres tablas DP02 tienen filas.
- [ ] `e4_p03_validar_productos_publicacion` registra 6 validaciones OK.
- [ ] `MET_*` incluye procesos y entidades de Etapa 4.
- [ ] Los dos tableros HTML se generan en `DOCS/etapa4/`.

## Tableros

| Archivo | Contenido |
|---|---|
| `DOCS/etapa4/tablero_dp01_ventas_geo_score.html` | KPIs, top países, segmentos de score con etiquetas legibles y evolución mensual como gráfico de línea |
| `DOCS/etapa4/tablero_dp02_dqm.html` | Validaciones, eventos, perfilado y validaciones recientes |

Los tableros no requieren dependencias externas. Son HTML/CSS estático generado
desde la base para que la entrega sea visual y reproducible.

Si `dqm_perfilado` no tiene filas en la base actual, `dp02_dqm_perfilado_resumen`
publica una fila explícita `sin_perfilado_disponible` para que el tablero DQM
muestre el estado real sin fallar por tabla vacía.
