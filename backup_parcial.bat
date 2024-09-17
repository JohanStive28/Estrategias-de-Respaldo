@echo off
REM Configura las variables de entorno
set ORACLE_SID=XE
set ORACLE_HOME=C:\app\johan\product\21c\dbhomeXE
set PATH=%ORACLE_HOME%\bin;%PATH%

REM Obtener la fecha y hora actual para crear un nombre de archivo único
set TIMESTAMP=%DATE:-4%_%DATE:-10,2%%DATE:~-7,2%%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%

REM Ejecutar el script RMAN para el backup de tablespaces específicos y agregar al archivo de log
rman target / @backup_parcial.rcat >> "C:\app\johan\product\21c\dbhomeXE\backups\backup_log.log" 2>&1
