# CLAUDE.md — Convenciones del proyecto mcd-ua-idw

> **Changelog (vs. versión anterior):**
> - Agregada sección "Orden de ejecución de scripts" — checklist manual a
>   mantener actualizado con cada script nuevo, porque la TUI no respeta
>   ningún orden de dependencias, solo lista lo que descubre.
> - Confirmada como regla definitiva (antes estaba sin acordar): los DDL
>   que crean o dropean tablas se ejecutan siempre manualmente por una
>   persona, nunca por un agente.

## Contexto

- TP de Data Warehousing (TPG01) sobre la base Northwind.
- 4 etapas: Adquisición, Ingeniería, Actualización, Publicación.
- Equipo de 2 personas.
- La consigna es la fuente de verdad. Ejemplos de otros grupos/años son solo referencia de formato — no copiar.

> **PENDIENTE**: Agregar `docs/TP_Consigna.pdf` y el to-do de Etapa 1 al repo.
> Cuando existan, importar con:
> ```
> @docs/TP_Consigna.pdf
> @docs/etapa1_todo.md
> ```

---

## Stack

- **Motor**: PostgreSQL 17 (Docker, vía `compose.yaml`).
- **ORM / migrations**: SQLAlchemy (async) + psycopg3 + Alembic.
- La consigna permite cualquier motor relacional estándar. Postgres es válido.
- **Regla clave**: la lógica de transformación DW vive en SQL. Python es solo orquestador.

---

## Contrato de scripts Python

Cada script en `src/mcd_ua_idw/scripts/` debe exponer:

```python
NAME: str      # opcional
VERSION: int
async def run(session: AsyncSession) -> dict: ...
```

- `run()` **no** hace commit/rollback — lo maneja `runner.py` vía `session_factory.begin()`.
- El dict de retorno debe ser serializable a JSON.
- `discover_scripts()` (en `script_runner/discovery.py`) recorre el paquete
  `mcd_ua_idw.scripts` con `iter_modules` y registra cualquier módulo que
  tenga `async def run(session)` + `VERSION` entero positivo. Por eso
  ningún archivo que no sea un script ejecutable debe vivir suelto en esa
  carpeta (ver patrón para scripts respaldados por SQL, abajo).

---

## Ejecución de scripts (verificado funcionando end-to-end)

- **CLI real**: `uv run idw-scripts` (`pyproject.toml`:
  `idw-scripts = "mcd_ua_idw.script_runner.tui:main"`). Es una TUI
  interactiva (Textual): muestra en un árbol los scripts que descubre
  `discover_scripts()`, agrupados por prefijo de módulo (`e<number>_` como
  "Etapa N", `util_` como "Utilidades", otros prefijos como grupo propio, y
  sin prefijo como "Otros"). Los grupos arrancan colapsados para no mostrar la
  lista completa de una vez; el usuario expande/contrae el grupo que necesita.
  Ejecuta el script hoja que el usuario selecciona con Enter. No corre todos
  automáticamente, y no admite target puntual por nombre desde la invocación.
- **Scripts respaldados por SQL**: el `.sql` se co-ubica con un wrapper
  `.py` fino en `src/mcd_ua_idw/scripts/` (mismo nombre base, ej.
  `crear_tablas_dqm.sql` + `crear_tablas_dqm.py`). El wrapper sigue el
  contrato normal y su `run()` solo llama a `run_sql_file`. El `.sql` es
  invisible para `discover_scripts()` (solo mira módulos Python).
- **`run_sql_file`**: existe en `src/mcd_ua_idw/script_runner/sql_utils.py`
  (no en `mcd_ua_idw.scripts`, para no contaminar el discovery):

```python
  async def run_sql_file(session: AsyncSession, path: Path) -> None:
      """Ejecuta el contenido completo de un archivo .sql en una sola
      sentencia multi-statement. No hace commit/rollback - lo maneja
      runner.py."""
      sql = Path(path).read_text(encoding="utf-8")
      await session.execute(text(sql))
```

- **Flujo confirmado**: `discover_scripts()` → TUI → `execute_script()` →
  `run_sql_file()` → DDL multi-statement en una sola transacción. Primer
  caso real: `crear_tablas_dqm.py` / `crear_tablas_dqm.sql`.

---

## Orden de ejecución de scripts (checklist manual — actualizar con cada script nuevo)

La TUI agrupa scripts por prefijo/etapa para facilitar la navegación, pero
**no** representa un plan de dependencias ejecutable automáticamente. Dentro
de cada grupo se ordena para lectura humana, pero quien vaya a ejecutar scripts
tiene que guiarse por este checklist y no por asumir que el árbol visual
define el flujo completo.

**Orden actual (Etapas 1-3 completas + Etapa 4 scripts escritos, pendiente ejecución manual):**

 1. `e0_p01_crear_tablas_dqm` — prerequisito absoluto; crea las 3 tablas DQM
 2. `e1_p01_crear_tablas_txt_sin_deps`
 3. `e1_p02_crear_tablas_tmp_sin_deps`
 4. `e1_p03_cargar_txt_sin_deps`
 5. `e1_p04_validar_tipos_sin_deps` — TP-3d + TP-3e (5 tablas sin deps)
 6. `e1_p05_perfilar_sin_deps` — TP-3f
 7. `e1_p06_cargar_tmp_sin_deps` — TP-3g; se bloquea si p04 tiene ERRORs
 8. `e1_p07_crear_tablas_txt_con_deps`
 9. `e1_p08_crear_tablas_tmp_con_deps`
10. `e1_p09_cargar_txt_con_deps`
11. `e1_p10_validar_tipos_con_deps` — TP-3d + TP-3e (6 tablas con deps)
12. `e1_p11_perfilar_con_deps` — TP-3f
13. `e1_p12_cargar_tmp_con_deps` — TP-3g; se bloquea si p10 tiene ERRORs
14. `e1_p13_validar_integridad_ref` — TP-3h; solo después de p12
15. `e2_p01_crear_tablas_metadata` — TP-5; crea soporte `MET_*`
16. `e2_p02_documentar_metadata_inicial` — TP-5/6/7; documenta Metadata base, DQM y modelo DWA propuesto
17. `e2_p03_crear_modelo_dwa` — TP-6/7; crea DWA, DWM y enriquecimiento inicial
18. `e2_p04_validar_carga_dwa` — TP-8a/8b; valida calidad/integración antes de cargar DWA
19. `e2_p05_cargar_dwa_inicial` — TP-8c; carga DWA inicial desde TMP validada
20. `e2_p06_perfilar_dwa` — TP-7/8; perfila tablas DWA/DWM/enriquecimiento cargadas
21. `e3_p01_crear_tablas_txt_ingesta2` — TP-9a; crea TXT_nov para 4 tablas de Ingesta2
22. `e3_p02_crear_tablas_tmp_ingesta2` — TP-9a; crea TMP_nov con tipos del DER
23. `e3_p03_cargar_txt_ingesta2` — TP-9a; carga CSVs Ingesta2 → TXT_nov (customers usa `,` no `;`)
24. `e3_p04_validar_tipos_ingesta2` — TP-9b; validaciones formato/PK en TXT_nov
25. `e3_p05_perfilar_ingesta2` — TP-9b; perfilado descriptivo TXT_nov
26. `e3_p06_cargar_tmp_ingesta2` — TP-9b; TXT_nov → TMP_nov; se bloquea si p04 tiene ERRORs
27. `e3_p07_validar_integridad_ingesta2` — TP-9b; FK checks TMP_nov vs TMP_ Ingesta1; solo después de corregir XXXXX→OLDWO
28. `e3_p08_actualizar_dwa` — TP-9c/f; SCD2 customers/products + INSERT nuevas órdenes; bloquea si p07 tiene ERRORs
29. `e3_p09_actualizar_enriquecimiento` — TP-9g; recalcula dwa_enr_* post-Ingesta2
30. `e3_p10_actualizar_dqm_metadata` — TP-9i/9j; registra procesos Etapa 3 en MET_
31. `e3_p11_integrar_world_data` — TP-10; enriquece dwa_dim_geography con 6 atributos de país. Re-ejecutar una vez para aplicar mapeo final `MX→Mexico` e ISO fallback `Ireland→IE`.
32. `e3_p12_integrar_customer_score` — TP-11; crea dwa_enr_customer_score con 83 scores
33. `e4_p01_crear_tablas_publicacion` — TP-12/13; crea tablas `DPxx_` para publicación y tablero DQM
34. `e4_p02_cargar_productos_publicacion` — TP-12; carga `dp01_ventas_geo_score` y resúmenes `dp02_dqm_*`
35. `e4_p03_validar_productos_publicacion` — TP-12/13; valida productos publicados y deja huella en DQM
36. `e4_p04_documentar_metadata_publicacion` — TP-12/13; registra Etapa 4 en Metadata
37. `e4_p05_generar_tableros_html` — TP-13; genera tableros HTML en `DOCS/etapa4/`

Utilidades (sin orden de dependencia, ejecutar cuando se necesiten):
- `util_db_check`
- `util_dummy`

Actualizar esta lista cada vez que se sume un script.

---

## Diseño del DQM (cerrado y verificado en Postgres)

3 tablas especializadas, no una genérica EAV ni una por cada tipo de
control — el criterio es el **grano**: evento de proceso, resultado de
chequeo, y estadística descriptiva son tres preguntas distintas con forma
distinta.

- **`dqm_eventos`**: huella de procesos de transformación/copia (requisito
  transversal "Se pide"). 1 fila por operación ejecutada sobre una tabla.
  Columnas: `tabla`, `tipo_evento`, `nombre_script`, `fecha_inicio`,
  `fecha_fin`, `registros_procesados`, `estado`, `observaciones`.
- **`dqm_validaciones`**: resultado de un control de calidad puntual.
  Cubre TP-3d (formato), TP-3e (PK), TP-3h (integridad referencial), y
  después TP-8a/8b/9. 1 fila por chequeo ejecutado. Columnas: `tabla`,
  `columna` (NULL si es a nivel tabla), `tipo_chequeo`, `nombre_script`,
  `fecha`, `total_filas_evaluadas`, `registros_afectados`,
  `indicador_calculado` (proporción, para TP-20), `umbral_aplicado`,
  `resultado` ('OK'/'ERROR'), `detalle`.
- **`dqm_perfilado`**: estadística descriptiva (TP-3f), no es pasa/no-pasa.
  1 fila por (tabla, columna) perfilada. Columnas: `tabla`, `columna`
  (NULL = métrica a nivel tabla), `nombre_script`, `fecha`, `total_filas`,
  `nulos`, `valores_distintos`, `valor_minimo`/`valor_maximo` (TEXT a
  propósito), `outliers_detectados`, `observaciones`.

**Decisión explícita**: ninguna tiene FK física a `Scripts`/`ScriptVersions`/
`ScriptRuns`. Se referencia el script por nombre (`nombre_script`, TEXT)
para no atar estas tablas a un esquema de tracking no confirmado en
detalle. Se puede agregar la FK real más adelante con `ALTER TABLE`.

DDL completo en `src/mcd_ua_idw/scripts/e0_p01_crear_tablas_dqm.sql`. Tablas
creadas y verificadas en la base de desarrollo.

---

## Orden de carga — 11 tablas de Ingesta 1 (por dependencias FK)

1. **Sin deps**: `categories`, `suppliers`, `shippers`, `regions`, `customers`
2. **Autorreferencia**: `employees` (FK a sí misma vía `reportsTo`)
3. **Dependen de (1)**: `products` (→ categories, suppliers), `territories` (→ regions)
4. **Dependen de (2)+(3)**: `employee_territories` (→ employees, territories)
5. **Dependen de (1)**: `orders` (→ customers, employees, shippers)
6. **Dependen de (5)**: `order_details` (→ orders, products)

---

## Hallazgos de calidad de datos — no re-descubrir

- **`customers.csv`**: 11 columnas vienen pegadas en una sola, separadas por `;`. Resolver el split al bajar a TXT.
- **`employees.reportsTo`**: el DER espera FK entera, el CSV la infiere como `Float` (por nulos del gerente sin jefe).

---

## Estado actual del repo (actualizado 2026-07-02)

| Componente | Estado |
|---|---|
| Inventario (`Scripts` / `ScriptVersions`) | Existe y funciona — se autopuebla desde `runner.py` |
| LOG (`ScriptRuns`) | Existe y funciona |
| Columnas `descripcion` y `autor` en inventario | **Faltan** — pendiente agregar (to-do Etapa 1) |
| Diseño de tablas DQM | **Cerrado** (3 tablas, ver sección "Diseño del DQM") |
| Tablas DQM (creación física) | **Creadas y verificadas** en Postgres |
| `run_sql_file` | **Existe** en `script_runner/sql_utils.py`, verificado funcionando end-to-end |
| `track_decorator.py` | Stub vacío — decisión pendiente (ver TODO abajo) |
| `TXT_` — 11 tablas Ingesta 1 | **Creadas y cargadas** (e1_p01/p03/p07/p09) |
| `TMP_` — 11 tablas Ingesta 1 | **Creadas y cargadas** con CASTs (e1_p02/p06/p08/p12) |
| Validaciones DQM (TP-3d/3e) | **Completas** — 65 checks, todos OK (e1_p04/p10) |
| Perfilado DQM (TP-3f) | **Completo** — 83 columnas perfiladas (e1_p05/p11) |
| Integridad referencial (TP-3h) | **Completa** — 11 FKs, ningún huérfano (e1_p13) |
| Metadata Etapa 2 (TP-5) | **Scripts creados; usuario reportó ejecución manual 2026-06-28** — `met_entidades`, `met_atributos`, `met_procesos`, `met_indicadores_calidad` (e2_p01/e2_p02). Re-ejecutar e2_p02 si se quiere refrescar Metadata con ajustes posteriores. |
| Diseño DWA Etapa 2 (TP-6/7/8) | **Scripts creados, re-ejecutados manualmente y verificados 2026-06-28 21:35 UTC** — e2_p03 crea DWA/DWM/enriquecimiento con `dwa_dim_geography` y stock de producto; e2_p04 tiene 16 validaciones OK; e2_p05 conteo fact OK; e2_p06 perfila geografía + stock. Verificación: `dwa_dim_geography=102`, `dwa_fact_order_lines=2155`, `dwa_enr_customer_sales_metrics=89`, `dwa_enr_product_sales_metrics=77`. |
| Etapa 3 (TP-9/10/11) | **Ejecutada y verificada 2026-07-02 02:47-02:48 UTC** — e3_p01 a e3_p12 terminaron OK después de corregir `XXXXX→OLDWO`. Verificación: `dwa_fact_order_lines=2169`, `dwm_customer_history (es_vigente=false)=2`, `dwm_product_history (es_vigente=false)=3`, `dwa_enr_customer_score=83`, validaciones E3 OK y 0 afectadas. Pendiente: re-ejecutar `e3_p11_integrar_world_data` una vez por ajuste posterior de mapeo `MX→Mexico` e ISO `Ireland→IE`. |
| Etapa 4 (TP-12/13) | **Scripts y docs creados; pendiente ejecución manual** — publica `dp01_ventas_geo_score`, resúmenes `dp02_dqm_*`, validaciones DQM, Metadata y tableros HTML en `DOCS/etapa4/`. |

> Nota: la migración `9ea5f62ecfe7` se llama "dqm_tracking_models" pero crea las tablas de tracking (`Scripts`, `ScriptVersions`, `ScriptRuns`), no las de calidad de datos.

---

## TODO — decisiones pendientes (no tomar sin acuerdo de equipo)

- [x] Prefijos de capa: confirmados y documentados en `docs/decisiones_de_diseno.md`.
- [x] Formato de encabezado estándar para scripts SQL: `Nombre / Descripcion / Fecha / Autor / Version` — aplicado en todos los `.sql` de Etapa 1.
- [ ] `track_decorator.py`: borrar o implementar.
- [ ] Agregar `docs/TP_Consigna.pdf` y to-do de Etapa 1 al repo.
- [ ] Agregar columnas `descripcion` y `autor` a `Scripts`/`ScriptVersions` (migración Alembic chica).
- [x] Confirmar decisión sobre `freight` en DWA: se conserva como `order_freight_amount` no aditivo en el hecho de líneas; no se prorratea en Etapa 2.
- [x] Confirmar si dimensión geográfica se crea en Etapa 2 o espera a Ingesta2/Etapa 3 con `world-data-2023.csv`: se crea geografía básica con Ingesta 1 en Etapa 2; `world-data-2023.csv` queda como enriquecimiento externo de Etapa 3.

---

## Reglas de trabajo

- Decisiones de diseño se discuten y documentan **antes** de implementar. No avanzar etapas sin acuerdo.
- Todo lo no especificado por la consigna: decidirlo y registrarlo en `docs/decisiones.md` — no dejarlo solo en un chat.
- Commits por tarea puntual. Referenciar la etapa o ítem de rúbrica en el mensaje cuando aplique.
- **Los scripts DDL que crean o dropean tablas (`CREATE TABLE`, `DROP TABLE`)
  se ejecutan siempre manualmente, desde la TUI (`uv run idw-scripts`), por
  una persona del equipo — nunca de forma automática por un agente.** Un
  agente (Claude Code u otro) puede proponer y escribir el código del
  script; el paso que efectivamente cambia el estado de la base lo dispara
  siempre un humano.
- Ante la duda sobre si algo documentado acá ya existe en el código,
  verificar contra el código real antes de asumir (ver corrección de
  `run_sql_file`, capítulo de Ejecución de scripts — pasó una vez, puede
  volver a pasar).
