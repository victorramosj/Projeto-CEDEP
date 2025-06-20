@echo off
set PGPASSWORD=HKhnFzXggtmylfsSKcPbVGfQEvataqYo

for /f %%i in ('wmic OS Get localdatetime ^| find "."') do set datetime=%%i
set datetime=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

REM Backup apenas das tabelas de eventos e reservas (sem ocupacao)
pg_dump -U postgres -h shortline.proxy.rlwy.net -p 13741 -d railway -F c -b -v -f backup_railway_%datetime%.backup ^
-t eventos_evento ^
-t eventos_agendamento ^
-t eventos_agendamento_salas ^
-t eventos_sala ^
-t reservas_quarto ^
-t reservas_cama ^
-t reservas_hospede ^
-t reservas_reserva

echo Backup concluído: backup_railway_%datetime%.backup
pause