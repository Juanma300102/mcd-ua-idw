# Etapa 2 — Ingeniería

Etapa 2 convierte las tablas TMP validadas de Ingesta1 en un DWA dimensional documentado, con soporte de Metadata, Memoria, Enriquecimiento y controles DQM antes de cargar datos analíticos.

## Fuente de requerimientos

| Punto | Requisito de la consigna | Decisión de trabajo |
|---|---|---|
| 5 | Crear soporte para Metadata y describir entidades | Crear tablas `MET_*` y registrar entidades, atributos, procesos e indicadores |
| 6 | Definir y crear modelo dimensional DWA, con Memoria y Enriquecimiento | Modelo estrella de ventas a grano línea de orden, con `DWM_*` para historia y `DWA_ENR_*` para derivados |
| 7 | Diseñar/crear DQM para procesos DWA, descriptivos e indicadores | Reusar `dqm_eventos`, `dqm_validaciones`, `dqm_perfilado`; documentar su diseño en Metadata |
| 8 | Carga inicial del DWA desde TMP validada | Cargar solo si los umbrales DQM de Etapa 1/2 pasan; registrar huellas en DQM |

## Quick path

1. Ejecutar manualmente `e2_p01_crear_tablas_metadata` para crear soporte `MET_*`.
2. Ejecutar manualmente `e2_p02_documentar_metadata_inicial` para registrar Metadata base y diseño DWA propuesto.
3. Ejecutar manualmente `e2_p03_crear_modelo_dwa` para crear DWA/DWM/enriquecimiento.
4. Ejecutar `e2_p04_validar_carga_dwa` para registrar validaciones DQM de integración.
5. Ejecutar `e2_p05_cargar_dwa_inicial` para cargar DWA desde tablas `TMP_` ya validadas.
6. Ejecutar `e2_p06_perfilar_dwa` para registrar perfilado descriptivo del DWA.

> Como regla del proyecto, los scripts con `CREATE TABLE`/`DROP TABLE` se escriben en el repo pero los ejecuta manualmente una persona desde `uv run idw-scripts`.

## Modelo dimensional propuesto

| Tabla | Capa | Grano | Fuente principal |
|---|---|---|---|
| `dwa_dim_date` | DWA | 1 fila por fecha calendario usada en órdenes | Fechas de `tmp_orders` |
| `dwa_dim_geography` | DWA | 1 fila por combinación geográfica de Ingesta 1 | `tmp_customers`, `tmp_employees`, `tmp_orders` |
| `dwa_dim_customer` | DWA | 1 fila por cliente vigente con referencia geográfica | `tmp_customers` |
| `dwa_dim_product` | DWA | 1 fila por producto vigente, denormalizando categoría, proveedor y stock | `tmp_products`, `tmp_categories`, `tmp_suppliers` |
| `dwa_dim_employee` | DWA | 1 fila por empleado vendedor vigente con referencia geográfica | `tmp_employees` |
| `dwa_dim_shipper` | DWA | 1 fila por transportista | `tmp_shippers` |
| `dwa_fact_order_lines` | DWA | 1 fila por línea de orden (`order_id`, `product_id`) | `tmp_orders`, `tmp_order_details` |
| `dwm_customer_history` | DWM | Historia de atributos relevantes del cliente | `tmp_customers` |
| `dwm_product_history` | DWM | Historia de atributos relevantes del producto | `tmp_products` + lookup |
| `dwa_enr_customer_sales_metrics` | DWA/enriquecimiento | Métricas derivadas por cliente con ventas | DWA fact + dimensiones |
| `dwa_enr_product_sales_metrics` | DWA/enriquecimiento | Métricas derivadas por producto | DWA fact + dimensiones |

### Grano del hecho principal

`dwa_fact_order_lines` usa el grano más atómico disponible: una fila por detalle de orden. Esto permite publicar métricas por cliente, producto, empleado, transportista y tiempo sin perder detalle.

Medidas iniciales:

- `quantity`
- `unit_price`
- `discount`
- `gross_amount = unit_price * quantity`
- `discount_amount = unit_price * quantity * discount`
- `net_amount = gross_amount - discount_amount`
- `order_freight_amount` conserva el flete de cabecera de la orden como atributo no aditivo. Se repite en cada línea solo para navegación; no debe sumarse a grano línea ni se prorratea en Etapa 2.

### Alcance geográfico

En Etapa 2 se crea `dwa_dim_geography` con la información geográfica disponible
en Ingesta 1: país, región, ciudad y código postal de clientes, empleados y
destinos de envío de órdenes. La dimensión permite navegar ventas por geografía
de cliente y de envío. El enriquecimiento externo con `world-data-2023.csv`
queda para Etapa 3.

### Alcance de stock

En Etapa 2 se promueven atributos de stock de `tmp_products` a
`dwa_dim_product` y `dwm_product_history`: `units_in_stock`, `units_on_order`,
`reorder_level` y `stock_alarm_level`. El indicador `stock_alarm_level` usa
`0 = normal`, `1 = bajo/reorden` y `2 = agotado`.

### Métricas de ventas por cliente

`dwa_enr_customer_sales_metrics` se define como un enriquecimiento de clientes
con ventas: contiene una fila por cliente que aparece en `dwa_fact_order_lines`.
No se zero-fillan clientes sin órdenes, porque esos clientes ya existen en
`dwa_dim_customer` y esta tabla resume actividad comercial observada.

Referencia de apoyo: `DOCS/TP anteriores de ejemplo/ejemplo/TP DWA informe
ejemplo.pdf`, sección 4.1 "Métricas Calculadas Implementadas" (página 5 del
PDF), usa la capa DWA para métricas derivadas orientadas a BI; sección 9.2
(página 8) recomienda documentar fórmulas exactas en Metadata. Esa referencia
apoya el enfoque de enriquecimiento, pero la regla "solo clientes con ventas"
es decisión de este proyecto.

## Calidad antes de cargar DWA

| Control | Tabla DQM | Criterio inicial |
|---|---|---|
| Etapa 1 sin errores pendientes | `dqm_validaciones` | 0 errores para validaciones de `TXT_`/`TMP_` requeridas |
| Integridad de joins DWA | `dqm_validaciones` | 0 claves sin dimensión correspondiente |
| Geografía básica disponible | `dqm_validaciones` | país no vacío en clientes, empleados y envíos |
| Stock válido | `dqm_validaciones` | stock/reorden no nulos ni negativos |
| Conteos fuente vs destino | `dqm_validaciones` | cantidad fact = cantidad `tmp_order_details` |
| Perfilado DWA | `dqm_perfilado` | registrar totales, nulos, distintos y rangos de tablas DWA |
| Huella de carga | `dqm_eventos` | 1 evento por tabla/capa cargada |

## Checklist de scripts

| Orden | Script | Estado |
|---:|---|---|
| 15 | `e2_p01_crear_tablas_metadata` | usuario reportó ejecución manual 2026-06-28 |
| 16 | `e2_p02_documentar_metadata_inicial` | re-ejecutado manualmente 2026-06-28 21:35 UTC; Metadata geografía + stock verificada |
| 17 | `e2_p03_crear_modelo_dwa` | re-ejecutado manualmente 2026-06-28 21:35 UTC; DWA geografía + stock creado |
| 18 | `e2_p04_validar_carga_dwa` | re-ejecutado manualmente 2026-06-28 21:35 UTC; 16 validaciones OK |
| 19 | `e2_p05_cargar_dwa_inicial` | re-ejecutado manualmente 2026-06-28 21:35 UTC; carga y conteo fact OK |
| 20 | `e2_p06_perfilar_dwa` | re-ejecutado manualmente 2026-06-28 21:35 UTC; perfiles geografía + stock verificados |

Verificación read-only posterior:

- `dwa_dim_geography`: 102 filas.
- `dwa_fact_order_lines`: 2155 filas.
- `dwa_enr_customer_sales_metrics`: 89 clientes con ventas.
- `dwa_enr_product_sales_metrics`: 77 productos.
- `e2_p04_validar_carga_dwa`: 16 validaciones vigentes OK, 0 afectados.
- `e2_p05_cargar_dwa_inicial`: `DWA_CONTEO_FACT` OK, 0 afectados.

## Decisión de atributos

Cerrado para Etapa 2: pasan al DWA los atributos ya implementados más
geografía de Ingesta 1 y stock de producto. El resto queda en TMP/Memoria o
como candidato futuro.

### Lista de atributos evaluados

Usar esta matriz para cerrar la decisión pendiente de atributos. La columna
"Destino recomendado" refleja el modelo ya implementado cuando aplica; las filas
marcadas como "opcional" son candidatas que el equipo puede promover si aportan
valor analítico al informe, tableros o Etapa 3.

| Fuente TMP | Atributos | Destino recomendado | Motivo / decisión a tomar |
|---|---|---|---|
| `tmp_customers` | `customer_id`, `company_name` | `dwa_dim_customer` + `dwm_customer_history` | Identidad natural y nombre comercial del cliente; mantener en DWA y Memoria. |
| `tmp_customers` | `contact_name`, `contact_title` | `dwa_dim_customer` + `dwm_customer_history` | Útil para navegación comercial; decidir si se considera atributo analítico o solo descriptivo. |
| `tmp_customers` | `city`, `region`, `postal_code`, `country` | `dwa_dim_customer` + `dwm_customer_history` + `dwa_dim_geography` | Geografía básica priorizada en Etapa 2; enriquecimiento externo queda para Etapa 3. |
| `tmp_customers` | `phone`, `fax` | `dwa_dim_customer` + `dwm_customer_history` | Dato descriptivo/contacto; puede quedar en DWA por trazabilidad o moverse a solo Memoria/TMP si se quiere reducir PII. |
| `tmp_customers` | `address` | Opcional: `dwm_customer_history` o solo TMP | Dirección completa no se usa en métricas actuales; incluir solo si el informe requiere trazabilidad detallada del cliente. |
| `tmp_products` + lookups | `product_id`, `product_name`, `category_id`, `category_name`, `supplier_id`, `supplier_name` | `dwa_dim_product` + `dwm_product_history` | Identidad y navegación principal de producto/categoría/proveedor. |
| `tmp_products` | `quantity_per_unit`, `unit_price`, `discontinued` | `dwa_dim_product` + `dwm_product_history` | Atributos comerciales del producto; `unit_price` también sirve como atributo vigente, aunque el precio histórico de venta está en el hecho. |
| `tmp_products` | `units_in_stock`, `units_on_order`, `reorder_level` | `dwa_dim_product` + `dwm_product_history` | Se prioriza stock en Etapa 2; además se deriva `stock_alarm_level`. |
| `tmp_categories` | `description` | Opcional: `dwa_dim_product` o solo TMP | Descripción de categoría; baja prioridad para métricas de ventas, útil solo como descriptor. |
| `tmp_suppliers` | `contact_name`, `contact_title`, `address`, `city`, `region`, `postal_code`, `country`, `phone`, `fax`, `home_page` | Opcional: futura `dwa_dim_supplier` o solo TMP | Hoy solo se denormaliza `supplier_name` en producto. Promover si se crearán productos de datos por proveedor o geografía de proveedor. |
| `tmp_employees` | `employee_id`, `first_name`, `last_name`, `title`, `city`, `region`, `country`, `reports_to` | `dwa_dim_employee` + `dwa_dim_geography` | Dimensión de vendedor; `first_name` + `last_name` se consolida como `employee_name`. |
| `tmp_employees` | `hire_date`, `birth_date` | Opcional: `dwa_dim_employee` o futura Memoria de empleado | Útil para antigüedad/edad del empleado, pero no necesario para ventas iniciales. |
| `tmp_employees` | `title_of_courtesy`, `address`, `postal_code`, `home_phone`, `extension`, `notes`, `photo_path` | Solo TMP, salvo decisión explícita | Datos operativos o sensibles con bajo valor analítico para DWA inicial. |
| `tmp_shippers` | `shipper_id`, `company_name`, `phone` | `dwa_dim_shipper` | Dimensión completa de transportista disponible en Ingesta 1. |
| `tmp_orders` | `order_id`, `customer_id`, `employee_id`, `ship_via`, `order_date`, `required_date`, `shipped_date`, `freight` | `dwa_fact_order_lines` + `dwa_dim_date` | Claves, fechas y flete necesarios para el hecho. `freight` queda como `order_freight_amount` no aditivo. |
| `tmp_orders` | `ship_city`, `ship_region`, `ship_postal_code`, `ship_country` | `dwa_dim_geography` + `dwa_fact_order_lines` | Se prioriza geografía de envío en Etapa 2. |
| `tmp_orders` | `ship_name`, `ship_address` | Solo TMP, salvo decisión explícita | Datos operativos de envío; no se agregan en este cambio. |
| `tmp_order_details` | `order_id`, `product_id`, `unit_price`, `quantity`, `discount` | `dwa_fact_order_lines` | Grano y medidas base del hecho; ya cargados. |
| `tmp_regions`, `tmp_territories`, `tmp_employee_territories` | `region_id`, `region_description`, `territory_id`, `territory_description`, `employee_id` | Opcional: futura dimensión/puente territorial o solo TMP | No participan del DWA inicial; promover solo si se necesita análisis territorial de empleados. |

Decisión de cierre para Etapa 2: promover geografía de Ingesta 1 y stock. No
promover por ahora shipping-delay metrics, supplier details ni employee tenure.

#### Aportes encontrados en ejemplos anteriores

Referencia revisada: `DOCS/TP anteriores de ejemplo/ejemplo/TP DWA informe
ejemplo.pdf` y `DOCS/TP anteriores de ejemplo/ejemplo/TP DWA presentacion
ejemplo.pdf`. Los scripts del ejemplo solo muestran una carga parcial de
`Categories` y no aportan una lista completa de atributos dimensionales.

| Aporte del ejemplo | Atributos/candidatos relacionados en este TP | Lectura para nuestra decisión |
|---|---|---|
| Modelo dimensional con dimensiones de país, fecha, transportista, proveedor, cliente, empleado y producto, más un hecho de ventas. | `country`, `ship_country`, atributos de `tmp_suppliers`, `tmp_shippers`, `tmp_customers`, `tmp_employees`, `tmp_products`, fechas de `tmp_orders`. | Refuerza que cliente/producto/empleado/transportista/fecha son núcleo DWA. Proveedor y país son buenos candidatos si se necesita más análisis, pero país/geografía queda mejor para Etapa 3 con `world-data-2023.csv`. |
| Métricas DWA calculadas para BI: ventas brutas/netas, descuentos, stock crítico y demoras de envío. | `unit_price`, `quantity`, `discount`, `units_in_stock`, `units_on_order`, `reorder_level`, `discontinued`, `required_date`, `shipped_date`. | Refuerza mantener medidas de ventas ya cargadas. También sube prioridad de los campos de stock y del cálculo de demora (`shipped_date > required_date`) si queremos enriquecer más el DWA. |
| Productos de datos por país/fecha, stock crítico, envíos demorados, ventas por empleado y proveedores principales. | Shipping geography (`ship_city`, `ship_region`, `ship_country`), stock fields, employee dimension, supplier fields. | Sugiere cuatro grupos opcionales claros: geografía de envío, stock, desempeño de empleado y análisis de proveedor. |
| Metadata por capa con fórmulas, reglas, linaje y nomenclatura consistente. | Todos los atributos promovidos a DWA/DWM/enriquecimiento. | Cualquier atributo elegido debe registrarse en Metadata; no basta con agregarlo al DDL/carga. |

Conclusión: el equipo prioriza geografía de Ingesta 1 y stock para Etapa 2. Los
demás aportes del ejemplo quedan como futuros candidatos y no se agregan en este
cambio.
