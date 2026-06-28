# Decisiones de diseño — mcd-ua-idw

Registro de decisiones tomadas durante el desarrollo del TP de Data Warehousing (TPG01 — Northwind).
Actualizar este archivo cada vez que se tome una decisión relevante de diseño.

---

## Convenciones generales

### Prefijos de capa
Adoptados según recomendación de la consigna (punto 17):

| Prefijo | Capa |
|---|---|
| `TXT_` | Temporales sin formato — copia fiel del CSV, todos los campos TEXT |
| `TMP_` | Temporales validadas — tipos del DER, con PKs |
| `ING_` | Capa a ingestar (previo al DWA) |
| `DWA_` | Data Warehouse Analítico |
| `DQM_` | Data Quality Mart |
| `DWM_` | Memoria (SCD / historia de cambios) |
| `MET_` | Metadata |
| `DPxx_` | Productos de datos |

### Nombrado de scripts Python
- **Pipeline**: `e<etapa>_p<paso>_<descripcion>` (ej. `e1_p01_crear_tablas_txt_sin_deps`)
- **Utilidades/test**: `util_<descripcion>` (ej. `util_db_check`)
- Restricción técnica: los módulos Python no pueden empezar con dígito, por eso se usa letra prefix.

### Nombres de columnas en base de datos
- Siempre snake_case (ej. `category_id`, `company_name`).
- El mapeo desde los nombres camelCase de los CSVs (ej. `categoryID` → `category_id`) se hace explícitamente en el script Python de carga, no en SQL.

---

## Etapa 0 — Prerequisitos

### Diseño de tablas DQM
3 tablas especializadas por grano de información:
- `dqm_eventos`: huella de procesos de transformación/copia (1 fila por operación sobre una tabla)
- `dqm_validaciones`: resultado de controles de calidad puntuales (1 fila por chequeo)
- `dqm_perfilado`: estadística descriptiva por tabla/columna

**Alternativa descartada**: tabla única genérica EAV. Descartada porque mezclaría granos distintos y dificultaría las consultas analíticas posteriores.

### Ubicación de `run_sql_file`
Helper ubicado en `src/mcd_ua_idw/script_runner/sql_utils.py`, fuera del paquete `mcd_ua_idw/scripts/`.
**Motivo**: `discover_scripts()` usa `iter_modules` sobre `mcd_ua_idw.scripts` — cualquier módulo Python en esa carpeta que no exponga `async def run(session)` + `VERSION` generaría un error. Los helpers de infraestructura no deben contaminar el espacio de discovery.

---

## Etapa 1 — Adquisición

### Tablas del DER ausentes en ingesta1
Las siguientes tablas aparecen en el DER de Northwind pero no tienen CSV en ingesta1:
- `customer_customer_demo` (tabla de vínculo)
- `customer_demographics`
- `us_states`

**Decisión**: no se crean TXT_ ni TMP_ para ellas. La discrepancia queda documentada aquí y en el informe.

### Campos `picture` (categories) y `photo` (employees)
- **En TXT_**: se incluyen como TEXT (copia fiel del CSV — son strings hexadecimales tipo `0x151C2F...`).
- **En TMP_**: se excluyen.
- **Motivo**: son blobs OLE de SQL Server exportados como hex. No tienen valor analítico en el contexto de este DWA. Castearlos a BYTEA sería posible pero innecesario.

### Nulos en CSVs
Los CSVs representan valores nulos con el string literal `"NULL"` (no nulos reales de CSV).
**Decisión**: convertir `"NULL"` → `None` durante la carga en TP-3c (script `e1_p03_cargar_txt_sin_deps`).
Los registros en TXT_ quedan con `NULL` real de base de datos, no con el string.

### Separador de `customers.csv`
`customers.csv` usa `;` como separador (todos los demás usan `,`).
Adicionalmente tiene line endings CRLF.
**Decisión**: manejar con `delimiter=';'` y `newline=''` en el `open()` del script de carga.

### `territories.territory_id` — tipo TEXT
Los valores tienen ceros a la izquierda (ej. `'01581'`).
El DER Northwind lo define como `nvarchar(20)`.
**Decisión**: tipo TEXT en TMP_territories (no INTEGER). Castear a INTEGER perdería los ceros, y si bien en este dataset no cambia las FKs, mantener TEXT es más fiel al DER original.

### `products.discontinued` — tipo INTEGER
Valores en CSV: `'0'` y `'1'`.
**Decisión**: INTEGER en TMP_ (no BOOLEAN).
**Motivo**: SQL estándar no tiene tipo BOOLEAN nativo; INTEGER con valores 0/1 es más portable y compatible con la restricción TP-23 de SQL estándar.

### Mecanismo de carga CSV → TXT_
**Decisión**: `csv.DictReader` + `session.execute(text(...), lista_de_dicts)` (bulk insert SQLAlchemy).
**Alternativa descartada**: `COPY FROM` de psycopg. Requeriría acceder al driver raw connection fuera del contrato de sesión que maneja `runner.py`. La diferencia de performance es irrelevante para los volúmenes de ingesta1 (máx. 2155 filas).

### `orders.freight` — tipo NUMERIC
El DER muestra `freight` como `abc` (texto), pero el CSV contiene valores decimales (`32.38`, etc.).
**Decisión**: NUMERIC en TMP_orders. Se documenta como desvío entre DER y datos reales.

### `employees.reportsTo` — FK autorreferencial nullable
El CSV tiene el valor como entero para la mayoría de empleados, y `"NULL"` para el gerente general (sin jefe).
**Decisión**: INTEGER nullable en TMP_employees. El NULL se convierte con la misma lógica `"NULL"→None` del script de carga.

### Fechas — formato con milisegundos
Todas las fechas vienen como `1996-07-04 00:00:00.000` (timestamp con milisegundos).
PostgreSQL acepta este formato directamente al castear a TIMESTAMP desde TEXT.
**Decisión**: tipo TIMESTAMP en TMP_ para todas las columnas de fecha. No requiere transformación adicional.

### Alcance de restricción TP-23 ("solo SQL estándar")
La consigna recomienda SQLite pero permite cualquier motor relacional estándar.
**Interpretación adoptada**: la restricción aplica a los scripts SQL (no usar extensiones propietarias en DDL/DML). El código Python que orquesta la carga de CSVs no está alcanzado por esta restricción. PostgreSQL es válido como motor.

### TP-19: Umbrales de aceptación/rechazo — Etapa 1 completa (11 tablas)

**Criterio**: `umbral_aplicado = 0.0` (tolerancia cero) para todos los controles de las
11 tablas de Ingesta 1 — tanto las 5 sin dependencias FK como las 6 con dependencias.

**Justificación**: los datos Northwind son de referencia y volumen conocido (máx. 2155 filas).
Cualquier error de formato, PK o FK indica un problema en la carga TXT_, no un dato ambiguo aceptable.

**Regla de resultado**: `'OK'` si `registros_afectados == 0`; `'ERROR'` en caso contrario.
Los scripts de carga TMP_ (`e1_p06`, `e1_p12`) se bloquean si hay algún `'ERROR'` previo
en `dqm_validaciones` para las tablas correspondientes.

### Catálogo de tipos de chequeo en dqm_validaciones

Todos los chequeos aplican solo sobre valores no-NULL cuando tiene sentido (ej. FORMATO_*
no cuenta NULLs como error de formato; la nullable se controla con NOT_NULL/PK_NULOS).

| tipo_chequeo | Condición de error | Scripts | Aplica a |
|---|---|---|---|
| `FORMATO_ENTERO` | `valor !~ '^\d+$'` | p04, p10 | Columnas que se castean a INTEGER en TMP_ |
| `FORMATO_NUMERICO` | `valor !~ '^\d+(\.\d+)?$'` | p10 | Columnas NUMERIC en TMP_ (precios, freight, discount) |
| `FORMATO_TIMESTAMP` | `valor !~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$'` | p10 | Columnas TIMESTAMP en TMP_ |
| `NOT_NULL` | `columna IS NULL` | p04, p10 | Columnas declaradas NOT NULL en TMP_ |
| `PK_NULOS` | `pk_col IS NULL` | p04, p10 | Cada columna que integra la PK (incluidas PKs compuestas) |
| `PK_DUPLICADOS` | combinación duplicada | p04, p10 | PK simple o compuesta (ver decisión abajo) |
| `FK_INTEGRIDAD` | valor FK sin padre en TMP_ | p13 | Columnas FK en las 6 tablas con dependencias |

Para `PK_DUPLICADOS` en PKs compuestas, el campo `columna` en `dqm_validaciones` usa
el formato `"col1|col2"` (separador `|`) como convención de display.

### PKs compuestas en TMP_

Dos tablas tienen clave primaria de dos columnas:

| Tabla | PK |
|---|---|
| `tmp_employee_territories` | `(employee_id, territory_id)` |
| `tmp_order_details` | `(order_id, product_id)` |

**Decisión**: se definen con `PRIMARY KEY (col1, col2)` en el DDL de TMP_. No hay tabla
de FK que las referencie en Ingesta 1, por lo que no hay implicaciones adicionales.

### Sin FK constraints físicas en TMP_

Las tablas TMP_ no declaran `FOREIGN KEY` a nivel base de datos.
**Motivo**: TMP_ es una capa de staging temporal antes de ING_. Agregar FK constraints
complicaría el orden de carga (habría que respetar exactamente el orden de dependencias
a nivel transacción) sin beneficio real, ya que la integridad se verifica de todas formas
con `e1_p13_validar_integridad_ref` (tipo `FK_INTEGRIDAD` en `dqm_validaciones`).

### `order_details` — tipos numéricos

| Columna | Tipo en TMP_ | Valores observados |
|---|---|---|
| `unit_price` | NUMERIC | `14.00`, `9.80`, `34.80` … |
| `quantity` | INTEGER | enteros positivos |
| `discount` | NUMERIC | `0`, `0.05`, `0.15` … (incluye entero `0` sin punto decimal) |

La regex de FORMATO_NUMERICO (`^\d+(\.\d+)?$`) cubre tanto `0` como `0.05`. ✓

---

## Etapa 2 — Ingeniería

### Soporte de Metadata

Se crea una capa `MET_` con cuatro tablas iniciales:

| Tabla | Grano |
|---|---|
| `met_entidades` | 1 fila por entidad documentada |
| `met_atributos` | 1 fila por atributo de entidad |
| `met_procesos` | 1 fila por script/proceso del flujo DWA |
| `met_indicadores_calidad` | 1 fila por regla/indicador de calidad |

**Decisión**: la Metadata documenta tanto entidades físicas ya creadas como entidades planificadas del DWA. Esto permite cumplir la consigna de documentar el diseño antes de ejecutar DDL de DWA.

### Modelo dimensional inicial

El DWA inicial se diseña como modelo estrella de ventas con grano de línea de orden:

- Hecho principal: `dwa_fact_order_lines`, 1 fila por (`order_id`, `product_id`).
- Dimensiones iniciales: `dwa_dim_date`, `dwa_dim_customer`, `dwa_dim_product`, `dwa_dim_employee`, `dwa_dim_shipper`.
- Medidas derivadas: `gross_amount`, `discount_amount`, `net_amount`.

**Motivo**: el detalle de línea de orden es el grano más bajo disponible y permite agregaciones posteriores por cliente, producto, empleado, transportista y tiempo sin perder información.

### Capa de Memoria

Se crean entidades de memoria planificadas para los atributos que probablemente cambien en Ingesta2:

- `dwm_customer_history`
- `dwm_product_history`

**Decisión**: usar formato tipo SCD2 con vigencia (`vigente_desde`, `vigente_hasta`, `es_vigente`) cuando se implemente el DDL. En carga inicial habrá una única versión vigente por entidad natural.

### Capa de Enriquecimiento

El enriquecimiento se modela dentro del espacio DWA con prefijo `dwa_enr_*` porque la consigna no define un prefijo separado para enriquecimiento.

Entidades iniciales planificadas:

- `dwa_enr_customer_sales_metrics`
- `dwa_enr_product_sales_metrics`

**Motivo**: son datos derivados del hecho DWA, útiles para productos de datos posteriores, no datos fuente ni staging.

**Referencia de apoyo**: el ejemplo anterior en
`DOCS/TP anteriores de ejemplo/ejemplo/TP DWA informe ejemplo.pdf`, sección
4.1 "Métricas Calculadas Implementadas" (página 5 del PDF), describe que la
capa DWA agrega métricas derivadas para reducir procesamiento en consultas y
soportar BI. La sección 9.2 (página 8) también recomienda documentar fórmulas
exactas de métricas calculadas en Metadata. Se usa solo como referencia de
formato/enfoque, no como fuente de verdad del TP actual.

### Métricas de ventas por cliente

**Decisión**: `dwa_enr_customer_sales_metrics` contiene solo clientes con al
menos una venta/orden.

**Motivo**: la entidad es un enriquecimiento de ventas, no una extensión de la
dimensión completa de clientes. Los clientes sin ventas quedan representados en
`dwa_dim_customer`, pero no se insertan con métricas en cero en esta tabla.

**Referencia de origen de la discusión**: la decisión surgió después de revisar
el ejemplo anterior citado arriba y de verificar la carga local de Etapa 2
(`91` clientes en `dwa_dim_customer` contra `89` clientes con ventas en
`dwa_enr_customer_sales_metrics`). El ejemplo apoya el uso de métricas derivadas
para BI, pero el alcance "solo clientes con ventas" es una decisión propia del
equipo para este TP.

### DQM para Etapa 2

Se reutilizan las tablas DQM existentes (`dqm_eventos`, `dqm_validaciones`, `dqm_perfilado`).

**Decisión**: no crear nuevas tablas DQM para Etapa 2 por ahora. El diseño de tres granos ya cubre eventos de carga DWA, validaciones de integración y perfilado dimensional. La Metadata (`met_indicadores_calidad`) registra qué indicadores y umbrales aplican.

### `freight` en el hecho

`freight` pertenece a la cabecera de orden y no a cada línea.

**Decisión**: conservarlo en `dwa_fact_order_lines` como `order_freight_amount`, un atributo no aditivo de cabecera repetido por línea solo para navegación.

**Motivo**: no hay una regla de negocio acordada para prorratear flete entre líneas, y crear un segundo hecho de orden agrega complejidad que no es necesaria para la carga inicial de Etapa 2.

**Regla de uso**: no sumar `order_freight_amount` directamente a grano línea. Para análisis de flete, agrupar/deduplicar primero por `order_id` o esperar un producto de datos específico.

### Dimensión geográfica

**Decisión**: crear una dimensión geográfica básica en Etapa 2 con datos de
Ingesta 1.

**Alcance**: `dwa_dim_geography` consolida combinaciones de
`country`/`region`/`city`/`postal_code` provenientes de clientes, empleados y
direcciones de envío de órdenes. En Etapa 2 no se agregan atributos externos de
`world-data-2023.csv`; ese enriquecimiento queda para Etapa 3.

**Motivo**: el ejemplo anterior prioriza análisis geográfico, y el equipo
decidió que Ingesta 1 ya contiene datos suficientes para soportar navegación
geográfica básica del DWA sin esperar a Ingesta 2.

### Stock en producto

**Decisión**: promover atributos de stock de `tmp_products` al DWA inicial.

**Alcance**: `dwa_dim_product` y `dwm_product_history` incluyen
`units_in_stock`, `units_on_order`, `reorder_level` y un indicador derivado
`stock_alarm_level` (`0` normal, `1` bajo/reorden, `2` agotado).

**Motivo**: el ejemplo anterior usa stock crítico como producto analítico, y los
campos necesarios ya están disponibles en Ingesta 1. No se agregan por ahora
shipping-delay metrics, dimensión detallada de proveedor ni antigüedad de
empleado.

### DWA físico inicial

El script `e2_p03_crear_modelo_dwa` crea el modelo físico inicial:

- Dimensiones: `dwa_dim_date`, `dwa_dim_geography`, `dwa_dim_customer`, `dwa_dim_product`, `dwa_dim_employee`, `dwa_dim_shipper`.
- Hecho: `dwa_fact_order_lines`.
- Memoria: `dwm_customer_history`, `dwm_product_history`.
- Enriquecimiento: `dwa_enr_customer_sales_metrics`, `dwa_enr_product_sales_metrics`.

**Decisión**: usar claves surrogate `GENERATED ALWAYS AS IDENTITY` en dimensiones/hecho y conservar claves naturales (`customer_id`, `product_id`, etc.) con `UNIQUE` para trazabilidad hacia TMP.

**Motivo**: separa identificadores analíticos de claves fuente y deja preparada la evolución SCD2 de Memoria en Etapa 3.
