-- Nombre: e2_p02_documentar_metadata_inicial
-- Descripcion: Registra Metadata inicial para el soporte MET, DQM existente
--              y modelo dimensional DWA/DWM/enriquecimiento propuesto.
-- Fecha: 2026-06-25
-- Autor: <equipo mcd-ua-idw>
-- Version: 0.1

-- NOTA: ejecutar despues de e2_p01_crear_tablas_metadata.

DELETE FROM met_atributos
WHERE entidad_id IN (
    SELECT id FROM met_entidades
    WHERE nombre IN (
        'met_entidades', 'met_atributos', 'met_procesos', 'met_indicadores_calidad',
        'dqm_eventos', 'dqm_validaciones', 'dqm_perfilado',
        'dwa_dim_date', 'dwa_dim_geography', 'dwa_dim_customer', 'dwa_dim_product', 'dwa_dim_employee',
        'dwa_dim_shipper', 'dwa_fact_order_lines', 'dwm_customer_history',
        'dwm_product_history', 'dwa_enr_customer_sales_metrics', 'dwa_enr_product_sales_metrics'
    )
);

DELETE FROM met_entidades
WHERE nombre IN (
    'met_entidades', 'met_atributos', 'met_procesos', 'met_indicadores_calidad',
    'dqm_eventos', 'dqm_validaciones', 'dqm_perfilado',
    'dwa_dim_date', 'dwa_dim_geography', 'dwa_dim_customer', 'dwa_dim_product', 'dwa_dim_employee',
    'dwa_dim_shipper', 'dwa_fact_order_lines', 'dwm_customer_history',
    'dwm_product_history', 'dwa_enr_customer_sales_metrics', 'dwa_enr_product_sales_metrics'
);

DELETE FROM met_procesos
WHERE nombre_script IN (
    'e2_p01_crear_tablas_metadata',
    'e2_p02_documentar_metadata_inicial',
    'e2_p03_crear_modelo_dwa',
    'e2_p04_validar_carga_dwa',
    'e2_p05_cargar_dwa_inicial',
    'e2_p06_perfilar_dwa'
);

DELETE FROM met_indicadores_calidad
WHERE tipo_chequeo IN (
    'DWA_SIN_ERRORES_PREVIOS',
    'DWA_FUENTE_NO_VACIA',
    'DWA_JOIN_DIMENSION',
    'DWA_FECHA_REQUERIDA',
    'DWA_GEOGRAFIA_REQUERIDA',
    'DWA_GRANO_FACT',
    'DWA_MEDIDA_VALIDA',
    'DWA_STOCK_VALIDO',
    'DWA_CONTEO_FACT',
    'DQM_INDICADOR_CALCULADO'
);

INSERT INTO met_entidades (nombre, capa, tipo_entidad, descripcion, grano, fuente)
VALUES
    ('met_entidades', 'MET', 'tabla', 'Catalogo de entidades del DWA y capas auxiliares.', '1 fila por entidad documentada', 'Etapa 2'),
    ('met_atributos', 'MET', 'tabla', 'Catalogo de atributos por entidad documentada.', '1 fila por atributo de entidad', 'Etapa 2'),
    ('met_procesos', 'MET', 'tabla', 'Catalogo de scripts/procesos relevantes del flujo DWA.', '1 fila por proceso/script', 'Etapa 2'),
    ('met_indicadores_calidad', 'MET', 'tabla', 'Catalogo de indicadores de calidad y reglas de aceptacion.', '1 fila por regla de calidad', 'Etapa 2'),
    ('dqm_eventos', 'DQM', 'tabla', 'Huella de procesos de transformacion/copia ejecutados.', '1 fila por evento de proceso sobre una tabla', 'Etapa 0'),
    ('dqm_validaciones', 'DQM', 'tabla', 'Resultado de controles de calidad puntuales.', '1 fila por chequeo ejecutado', 'Etapa 0'),
    ('dqm_perfilado', 'DQM', 'tabla', 'Estadisticas descriptivas por tabla/columna.', '1 fila por columna perfilada', 'Etapa 0'),
    ('dwa_dim_date', 'DWA', 'tabla_planificada', 'Dimension calendario para fechas de orden, requerida y envio.', '1 fila por fecha calendario', 'tmp_orders'),
    ('dwa_dim_geography', 'DWA', 'tabla_planificada', 'Dimension geografica basica de Ingesta 1 para clientes, empleados y envios.', '1 fila por combinacion country + region + city + postal_code', 'tmp_customers + tmp_employees + tmp_orders'),
    ('dwa_dim_customer', 'DWA', 'tabla_planificada', 'Dimension de clientes vigentes para analisis comercial con referencia geografica.', '1 fila por cliente vigente', 'tmp_customers'),
    ('dwa_dim_product', 'DWA', 'tabla_planificada', 'Dimension de productos vigentes con categoria, proveedor y atributos de stock.', '1 fila por producto vigente', 'tmp_products + tmp_categories + tmp_suppliers'),
    ('dwa_dim_employee', 'DWA', 'tabla_planificada', 'Dimension de empleados vendedores con referencia geografica.', '1 fila por empleado vigente', 'tmp_employees'),
    ('dwa_dim_shipper', 'DWA', 'tabla_planificada', 'Dimension de transportistas.', '1 fila por transportista', 'tmp_shippers'),
    ('dwa_fact_order_lines', 'DWA', 'tabla_planificada', 'Hecho principal de ventas a nivel linea de orden; freight se conserva como atributo no aditivo de cabecera.', '1 fila por order_id + product_id', 'tmp_orders + tmp_order_details'),
    ('dwm_customer_history', 'DWM', 'tabla_planificada', 'Memoria de cambios de atributos relevantes de clientes.', '1 fila por version historica de cliente', 'tmp_customers'),
    ('dwm_product_history', 'DWM', 'tabla_planificada', 'Memoria de cambios de atributos relevantes de productos.', '1 fila por version historica de producto', 'tmp_products'),
    ('dwa_enr_customer_sales_metrics', 'DWA', 'tabla_planificada', 'Enriquecimiento con metricas derivadas por cliente con ventas; no incluye clientes sin ordenes.', '1 fila por cliente con ventas', 'dwa_fact_order_lines'),
    ('dwa_enr_product_sales_metrics', 'DWA', 'tabla_planificada', 'Enriquecimiento con metricas derivadas por producto.', '1 fila por producto con metricas derivadas', 'dwa_fact_order_lines');

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'id', 'INTEGER', 1, 0, 0, 'Identificador surrogate interno.'
FROM met_entidades
WHERE nombre IN ('met_entidades', 'met_atributos', 'met_procesos', 'met_indicadores_calidad');

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'nombre', 'TEXT', 0, 0, 0, 'Nombre tecnico unico de la entidad.'
FROM met_entidades WHERE nombre = 'met_entidades';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'capa', 'TEXT', 0, 0, 0, 'Capa del flujo: TXT, TMP, ING, DWA, DQM, DWM, MET o DPxx.'
FROM met_entidades WHERE nombre = 'met_entidades';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'entidad_id', 'INTEGER', 0, 1, 0, 'Referencia a met_entidades.id.'
FROM met_entidades WHERE nombre = 'met_atributos';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'nombre_script', 'TEXT', 0, 0, 0, 'Nombre tecnico del script/proceso registrado.'
FROM met_entidades WHERE nombre = 'met_procesos';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'tipo_chequeo', 'TEXT', 0, 0, 0, 'Codigo del indicador o control de calidad.'
FROM met_entidades WHERE nombre = 'met_indicadores_calidad';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'id', 'INTEGER', 1, 0, 0, 'Identificador surrogate del evento DQM.'
FROM met_entidades WHERE nombre = 'dqm_eventos';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'tabla', 'TEXT', 0, 0, 0, 'Tabla o entidad procesada.'
FROM met_entidades WHERE nombre IN ('dqm_eventos', 'dqm_validaciones', 'dqm_perfilado');

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'resultado', 'TEXT', 0, 0, 0, 'Resultado del control: OK o ERROR.'
FROM met_entidades WHERE nombre = 'dqm_validaciones';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'indicador_calculado', 'NUMERIC', 0, 0, 1, 'Proporcion calculada para evaluar calidad.'
FROM met_entidades WHERE nombre = 'dqm_validaciones';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'date_key', 'INTEGER', 1, 0, 0, 'Clave calendario en formato YYYYMMDD.'
FROM met_entidades WHERE nombre = 'dwa_dim_date';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'geography_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de geografia en DWA.'
FROM met_entidades WHERE nombre = 'dwa_dim_geography';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'customer_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de cliente en DWA.'
FROM met_entidades WHERE nombre = 'dwa_dim_customer';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'customer_geography_key', 'INTEGER', 0, 1, 0, 'Referencia a dwa_dim_geography.geography_key.'
FROM met_entidades WHERE nombre = 'dwa_dim_customer';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'product_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de producto en DWA.'
FROM met_entidades WHERE nombre = 'dwa_dim_product';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'stock_alarm_level', 'INTEGER', 0, 0, 0, 'Indicador derivado de stock: 0 normal, 1 bajo/reorden, 2 agotado.'
FROM met_entidades WHERE nombre = 'dwa_dim_product';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'employee_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de empleado en DWA.'
FROM met_entidades WHERE nombre = 'dwa_dim_employee';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'employee_geography_key', 'INTEGER', 0, 1, 0, 'Referencia a dwa_dim_geography.geography_key.'
FROM met_entidades WHERE nombre = 'dwa_dim_employee';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'shipper_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de transportista en DWA.'
FROM met_entidades WHERE nombre = 'dwa_dim_shipper';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'order_line_key', 'INTEGER', 1, 0, 0, 'Clave surrogate de la linea de orden.'
FROM met_entidades WHERE nombre = 'dwa_fact_order_lines';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'ship_geography_key', 'INTEGER', 0, 1, 0, 'Referencia a la geografia de envio en dwa_dim_geography.'
FROM met_entidades WHERE nombre = 'dwa_fact_order_lines';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'net_amount', 'NUMERIC', 0, 0, 1, 'Importe neto derivado: unit_price * quantity * (1 - discount).'
FROM met_entidades WHERE nombre = 'dwa_fact_order_lines';

INSERT INTO met_atributos (entidad_id, nombre_atributo, tipo_dato, es_pk, es_fk, es_nullable, descripcion)
SELECT id, 'order_freight_amount', 'NUMERIC', 0, 0, 1, 'Importe de flete de cabecera, repetido por linea solo para navegacion; no es aditivo a grano linea.'
FROM met_entidades WHERE nombre = 'dwa_fact_order_lines';

INSERT INTO met_procesos (nombre_script, etapa, paso, tipo_proceso, capa_origen, capa_destino, descripcion, orden_ejecucion, requiere_validacion)
VALUES
    ('e2_p01_crear_tablas_metadata', 'Etapa 2', '5', 'DDL', NULL, 'MET', 'Crea soporte de Metadata.', 15, 0),
    ('e2_p02_documentar_metadata_inicial', 'Etapa 2', '5-7', 'METADATA', 'MET/DQM/DWA', 'MET', 'Documenta Metadata base, DQM y modelo DWA propuesto.', 16, 0),
    ('e2_p03_crear_modelo_dwa', 'Etapa 2', '6', 'DDL', NULL, 'DWA/DWM', 'Creara modelo dimensional, memoria y enriquecimiento.', 17, 1),
    ('e2_p04_validar_carga_dwa', 'Etapa 2', '8a-8b', 'DQM', 'TMP', 'DQM', 'Validara calidad e integracion antes de cargar DWA.', 18, 1),
    ('e2_p05_cargar_dwa_inicial', 'Etapa 2', '8c', 'CARGA_DWA', 'TMP', 'DWA/DWM', 'Cargara datos iniciales del DWA desde TMP validada.', 19, 1),
    ('e2_p06_perfilar_dwa', 'Etapa 2', '7/8', 'DQM', 'DWA', 'DQM', 'Perfilara tablas dimensionales y hechos cargados.', 20, 1);

INSERT INTO met_indicadores_calidad (tipo_chequeo, entidad, atributo, regla, umbral_aplicado, capa, descripcion)
VALUES
    ('DWA_SIN_ERRORES_PREVIOS', 'DWA', NULL, 'No deben existir validaciones ERROR pendientes para fuentes TMP requeridas.', 0.0, 'DWA', 'Bloquea carga DWA si la calidad previa no fue superada.'),
    ('DWA_FUENTE_NO_VACIA', 'tmp_orders/tmp_order_details', NULL, 'Las fuentes principales de hechos deben tener filas para cargar.', 0.0, 'DWA', 'Control de disponibilidad de fuentes para carga inicial.'),
    ('DWA_JOIN_DIMENSION', 'dwa_fact_order_lines', NULL, 'Cada FK del hecho debe resolver una dimension vigente o fuente base.', 0.0, 'DWA', 'Control de integracion dimensional.'),
    ('DWA_FECHA_REQUERIDA', 'tmp_orders', 'order_date|required_date', 'Las fechas obligatorias usadas por dwa_dim_date no deben ser nulas.', 0.0, 'DWA', 'Control de integracion con dimension calendario.'),
    ('DWA_GEOGRAFIA_REQUERIDA', 'tmp_customers/tmp_employees/tmp_orders', 'country|ship_country', 'Las fuentes geograficas basicas deben tener pais para construir dwa_dim_geography.', 0.0, 'DWA', 'Control de completitud geografica basica.'),
    ('DWA_GRANO_FACT', 'tmp_order_details', 'order_id|product_id', 'El grano de la fuente del hecho debe ser unico.', 0.0, 'DWA', 'Control de unicidad del hecho de lineas de orden.'),
    ('DWA_MEDIDA_VALIDA', 'tmp_order_details', 'unit_price|quantity|discount', 'Las medidas base deben ser no nulas y tener rangos validos.', 0.0, 'DWA', 'Control de consistencia de medidas antes de calcular importes.'),
    ('DWA_STOCK_VALIDO', 'tmp_products', 'units_in_stock|units_on_order|reorder_level', 'Los atributos de stock deben ser no nulos y no negativos.', 0.0, 'DWA', 'Control de consistencia de stock antes de cargar producto.'),
    ('DWA_CONTEO_FACT', 'dwa_fact_order_lines', NULL, 'Cantidad de filas del hecho debe igualar tmp_order_details cargado.', 0.0, 'DWA', 'Control de completitud de carga inicial.'),
    ('DQM_INDICADOR_CALCULADO', 'dqm_validaciones', 'indicador_calculado', 'Persistir proporcion de registros afectados sobre total evaluado.', 0.0, 'DQM', 'Indicador cuantitativo requerido por la consigna.');
