@echo off
set TIMESTAMP=%DATE:-4%_%DATE:-10,2%%DATE:~-7,2%%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
rman target / @backup_incremetal.rcv log="C:\app\Johan\product\21c\dbhomeXE\backups\LOG_%TIMESTAMP%.log"