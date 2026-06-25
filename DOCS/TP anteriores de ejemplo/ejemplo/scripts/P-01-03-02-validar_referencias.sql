-- Nombre: P-01-03-02-validar_referencias
-- Descripcion: Insercion tablas finales
-- Fecha: 2025-09-25
-- Autor: Coppolillo, Nestor
-- Version: 1.0

-- Insertar un registro en la tabla de scripts
INSERT INTO DWA_scripts (scriptID, scriptNombre,scriptDescripcion)
   VALUES(7,'P-01-03-02-validar_referencias','Validar las referencias cruzadas en las tablas de Northwind');
   
-- Crea registro en tabla de ejecuciones, con la fecha de inicio del script
insert into  DWA_ejec (scriptID, ejecTimestampInicio, ejecTimestampFin)
 VALUES(
       (select scriptID from DWA_scripts where scriptNombre = 'P-01-03-02-validar_referencias'),
        CURRENT_TIMESTAMP,
	    null);

-- Validaciones referencias cruzadas
-------------
-- Products	
-- Columna CategoryID
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Validacion referencia tabla Products, columna CategoryID',
        (select count(*) from Products
          where CategoryID not in (select CategoryID from Categories)), -- cantidad de errores
        CASE 
          WHEN (select count(*) from Products
          where CategoryID not in (select CategoryID from Categories)) > 0 THEN 0
          ELSE 1
		END  
        );

-- Registra la validacion exitosa
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Validacion referencia tabla Products - columna CategoryID exitoso',
        null,
        1);

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
