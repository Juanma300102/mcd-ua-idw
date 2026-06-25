-- Nombre: P-01-01-04-validar_tabla_categories
-- Descripcion: Valida los campos de la tabla
-- Fecha: 2025-09-18
-- Autor: Coppolillo, Nestor
-- Version: 1.0

-- Crea registro en tabla de ejecuciones, con la fecha de inicio del script
insert into  DWA_ejec (scriptID, ejecTimestampInicio, ejecTimestampFin)
 VALUES(
       (select scriptID from DWA_scripts where scriptNombre = 'P-01-01-04-validar_tabla_categories'),
        CURRENT_TIMESTAMP,
	    null);

-- Registra validaciones

-- Columna CategoryID
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Validacion tabla Categories_tmp, columna CategoryID',
        (SELECT count(*) FROM Categories_tmp WHERE CategoryID NOT GLOB '[0-9]*'), -- cantidad de errores
        CASE 
          WHEN (SELECT COUNT(*) FROM Categories_tmp WHERE CategoryID NOT GLOB '[0-9]*') > 0 THEN 0
          ELSE 1
		END  
        );

insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Validacion tabla Categories_tmp, columna CategoryID',
        (SELECT count(*) FROM Categories_tmp WHERE CategoryID IS NULL), -- cantidad de errores
        CASE 
          WHEN (SELECT COUNT(*) FROM Categories_tmp WHERE CategoryID IS NULL) > 0 THEN 0
          ELSE 1
		END  
        );
		

-- Columna CategoryName
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Validacion tabla Categories_tmp, columna CategoryName',
        (SELECT count(*) FROM Categories_tmp WHERE CategoryName IS NULL), -- cantidad de errores
        CASE 
          WHEN (SELECT COUNT(*) FROM Categories_tmp WHERE CategoryName IS NULL) > 0 THEN 0
          ELSE 1
		END  
        );
		
-- Agrego el resultado OK de la ejecucion
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Proceso exitoso',
        null,
        1);

-- Agrega la fecha de finalizacion del script
update DWA_ejec
set ejecTimestampFin = CURRENT_TIMESTAMP
where ejecID = (select max(ejecID) from DWA_ejec)
