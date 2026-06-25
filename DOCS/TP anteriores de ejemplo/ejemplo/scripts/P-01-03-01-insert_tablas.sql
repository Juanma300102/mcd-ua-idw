-- Nombre: P-01-03-01-insert_tablas
-- Descripcion: Insercion tablas finales
-- Fecha: 2025-09-25
-- Autor: Coppolillo, Nestor
-- Version: 1.0

-- Insertar un registro en la tabla de scripts
INSERT INTO DWA_scripts (scriptID, scriptNombre,scriptDescripcion)
   VALUES(6,'P-01-03-01-insert_tablas','Insercion en las tablas de Northwind');
   
-- Crea registro en tabla de ejecuciones, con la fecha de inicio del script
insert into  DWA_ejec (scriptID, ejecTimestampInicio, ejecTimestampFin)
 VALUES(
       (select scriptID from DWA_scripts where scriptNombre = 'P-01-03-01-insert_tablas'),
        CURRENT_TIMESTAMP,
	    null);

-- Inserta tablas

-------------
-- Categories	
INSERT INTO Categories (categoryID,categoryName,description,picture)
select 
    CAST(categoryID AS INTEGER),
    categoryName,
	description,
	picture
  from Categories_tmp;

-- Registra la Insercion exitosa
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Insercion tabla Categories exitoso',
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
