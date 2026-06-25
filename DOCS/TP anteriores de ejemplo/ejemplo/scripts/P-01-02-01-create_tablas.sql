-- Nombre: P-01-02-01-create_tablas
-- Descripcion: Creacion tablas finales
-- Fecha: 2025-09-25
-- Autor: Coppolillo, Nestor
-- Version: 1.0

-- Insertar un registro en la tabla de scripts
INSERT INTO DWA_scripts (scriptID, scriptNombre,scriptDescripcion)
   VALUES(5,'P-01-02-01-create_tablas','Creacion de las tablas de Northwind');
   
-- Crea registro en tabla de ejecuciones, con la fecha de inicio del script
insert into  DWA_ejec (scriptID, ejecTimestampInicio, ejecTimestampFin)
 VALUES(
       (select scriptID from DWA_scripts where scriptNombre = 'P-01-02-01-create_tablas'),
        CURRENT_TIMESTAMP,
	    null);

-- Crea tablas

-- Categories		
DROP TABLE IF EXISTS Categories;
CREATE TABLE Categories (
    CategoryID INTEGER PRIMARY KEY,
    CategoryName TEXT NOT NULL,
    Description TEXT,
    Picture BLOB
);

-- Registra la creacion exitosa
insert into DWA_DQM_ejec (ejecID, dqmejecMensaje, dqmejecCantidad, dqmejecError)
 VALUES((select max(ejecID) from DWA_ejec),
        'Creacion tabla Categories exitoso',
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


