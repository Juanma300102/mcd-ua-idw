
USE db_IDWTP;
GO

CREATE TABLE MET_DQM (
    nombre_tabla         VARCHAR(100),
    nombre_columna       VARCHAR(100),
    tipo_dato            VARCHAR(50),
    descripcion          VARCHAR(255),
    capa_dwh             VARCHAR(50),  -- ejemplos: staging, hechos, dimensión, memoria, enriquecimiento, DQM
    clave_primaria       BIT,
    clave_foranea        BIT,
    tabla_referencia     VARCHAR(100),
    columna_referencia   VARCHAR(100)
);

-- ===============================================
-- INSERCIÓN DE MET PARA TABLAS DQM
-- ===============================================

-- MET para tabla dqm_log
INSERT INTO MET_DQM (nombre_tabla, nombre_columna, tipo_dato, descripcion, capa_dwh, clave_primaria, clave_foranea, tabla_referencia, columna_referencia)
VALUES 
    ('dqm_log', 'id', 'INT IDENTITY(1,1)', 'Identificador único autoincremental del registro de log', 'DQM', 1, 0, NULL, NULL),
    ('dqm_log', 'tabla', 'VARCHAR(50)', 'Nombre de la tabla sobre la cual se ejecutó el chequeo de calidad', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'tipo_chequeo', 'VARCHAR(100)', 'Tipo de validación o chequeo de calidad ejecutado', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'descripcion', 'VARCHAR(255)', 'Descripción detallada del chequeo o resultado obtenido', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'registros_afectados', 'INT', 'Cantidad de registros que fueron afectados por el chequeo', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'fecha', 'DATETIME', 'Fecha y hora de ejecución del chequeo (valor por defecto: fecha actual)', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'accion', 'VARCHAR(50)', 'Tipo de acción ejecutada: Carga o Visualización', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'tablero', 'VARCHAR(100)', 'Nombre del tablero o dashboard asociado al log', 'DQM', 0, 0, NULL, NULL),
    ('dqm_log', 'usuario', 'VARCHAR(100)', 'Usuario que ejecutó la acción (puede ser nulo)', 'DQM', 0, 0, NULL, NULL);

-- MET para tabla dqm_eventos
INSERT INTO MET_DQM (nombre_tabla, nombre_columna, tipo_dato, descripcion, capa_dwh, clave_primaria, clave_foranea, tabla_referencia, columna_referencia)
VALUES 
    ('dqm_eventos', 'id', 'INT IDENTITY(1,1)', 'Identificador único autoincremental del evento', 'DQM', 1, 0, NULL, NULL),
    ('dqm_eventos', 'tabla', 'VARCHAR(50)', 'Nombre de la tabla involucrada en el evento', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'tipo_evento', 'VARCHAR(100)', 'Clasificación del evento: INICIO_CARGA, FIN_CARGA, INSERCION, ERROR_CARGA, etc.', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'descripcion', 'VARCHAR(255)', 'Descripción detallada del evento ocurrido', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'registros_procesados', 'INT', 'Cantidad de registros procesados durante el evento (valor por defecto: 0)', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'fecha_inicio', 'DATETIME', 'Fecha y hora de inicio del evento o proceso', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'fecha_fin', 'DATETIME', 'Fecha y hora de finalización del evento o proceso', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'fecha_registro', 'DATETIME', 'Fecha y hora de registro del evento en el log (valor por defecto: fecha actual)', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'duracion_segundos', 'INT (COMPUTED)', 'Duración calculada en segundos entre fecha_inicio y fecha_fin', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'estado', 'VARCHAR(50)', 'Estado del evento: EXITOSO, ERROR, EN_PROCESO', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'proceso', 'VARCHAR(100)', 'Nombre del proceso, job o procedimiento que generó el evento', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'usuario', 'VARCHAR(100)', 'Usuario responsable del proceso (puede ser nulo)', 'DQM', 0, 0, NULL, NULL),
    ('dqm_eventos', 'observaciones', 'VARCHAR(500)', 'Observaciones adicionales sobre el evento (puede ser nulo)', 'DQM', 0, 0, NULL, NULL);

-- ===============================================
-- VERIFICACIÓN DE LOS DATOS INSERTADOS
-- ===============================================

-- Consulta para verificar los metadatos insertados para las tablas DQM
SELECT 
    nombre_tabla,
    nombre_columna,
    tipo_dato,
    descripcion,
    capa_dwh,
    CASE WHEN clave_primaria = 1 THEN 'Sí' ELSE 'No' END as es_clave_primaria,
    CASE WHEN clave_foranea = 1 THEN 'Sí' ELSE 'No' END as es_clave_foranea
FROM MET_DQM 
WHERE capa_dwh = 'DQM'
ORDER BY nombre_tabla, nombre_columna;
