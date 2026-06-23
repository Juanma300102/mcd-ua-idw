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
  interactiva (Textual): lista los scripts que descubre `discover_scripts()`
  y ejecuta el que el usuario selecciona con Enter. No corre todos
  automáticamente, y no admite target puntual por nombre desde la
  invocación.
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

La TUI **no** respeta ningún orden de dependencias: lista lo que
`discover_scripts()` encuentra vía `iter_modules`, en el orden que el
discovery devuelva (no confirmado si es alfabético o de otro criterio —
no asumir nada sobre el orden visual de la lista). Por eso, quien vaya a
ejecutar scripts tiene que guiarse por este checklist y no por lo que
muestra la pantalla.

**Orden actual (al día de hoy, 1 script existente):**

1. `crear_tablas_dqm` — debe correrse primero, una sola vez. Es
   prerequisito de cualquier otro script de Etapa 1: los controles de
   calidad y las huellas de transformación que vienen después escriben en
   `dqm_eventos` / `dqm_validaciones` / `dqm_perfilado`, que tienen que
   existir antes.

**Criterio para cuando se agreguen los scripts de la Etapa 1 (loop de las
11 tablas):** el orden de ejecución debe espejar el orden de dependencias
FK ya documentado en "Orden de carga — 11 tablas de Ingesta 1" (más abajo
en este documento) — primero las tablas sin dependencias, después las que
dependen de ellas. Actualizar esta lista cada vez que se sume un script,
no dejarlo en la cabeza de quien lo escribió.

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

DDL completo en `src/mcd_ua_idw/scripts/crear_tablas_dqm.sql`. Tablas
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

## Estado actual del repo (verificado 2026-06-22)

| Componente | Estado |
|---|---|
| Inventario (`Scripts` / `ScriptVersions`) | Existe y funciona — se autopuebla desde `runner.py` |
| LOG (`ScriptRuns`) | Existe y funciona |
| Columnas `descripcion` y `autor` en inventario | **Faltan** — pendiente agregar (to-do Etapa 1) |
| Diseño de tablas DQM | **Cerrado** (3 tablas, ver sección "Diseño del DQM") |
| Tablas DQM (creación física) | **Creadas y verificadas** en Postgres |
| `run_sql_file` | **Existe** en `script_runner/sql_utils.py`, verificado funcionando end-to-end |
| `track_decorator.py` | Stub vacío — decisión pendiente (ver TODO abajo) |
| CSVs / tablas Northwind | No cargados en el repo todavía |

> Nota: la migración `9ea5f62ecfe7` se llama "dqm_tracking_models" pero crea las tablas de tracking (`Scripts`, `ScriptVersions`, `ScriptRuns`), no las de calidad de datos.

---

## TODO — decisiones pendientes (no tomar sin acuerdo de equipo)

- [ ] Prefijos de capa: confirmar cuáles usar (`TXT_`, `TMP_`, `ING_`, `DWA_`, `DQM_`, `DWM_`, `MET_`, `DPxx_`).
- [ ] Formato de encabezado estándar para cada script SQL (nombre / descripción / fecha / autor / versión).
- [ ] `track_decorator.py`: borrar o implementar.
- [ ] Agregar `docs/TP_Consigna.pdf` y to-do de Etapa 1 al repo.
- [ ] Agregar columnas `descripcion` y `autor` a `Scripts`/`ScriptVersions` (migración Alembic chica).

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
