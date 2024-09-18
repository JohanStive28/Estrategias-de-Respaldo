@echo off
REM Configura las variables de entorno
set ORACLE_SID=XE
set ORACLE_HOME=C:\app\johan\product\21c\dbhomeXE
set PATH=%ORACLE_HOME%\bin;%PATH%

REM Obtener la fecha y hora actual para crear un nombre de archivo único
set TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Ejecutar el script RMAN para el backup de tablespaces específicos y agregar al archivo de log
rman target / @backup_parcial.rcat >> "C:\app\johan\product\21c\dbhomeXE\backups\backup_total_%TIMESTAMP%.log"

echo Backup total completado.
