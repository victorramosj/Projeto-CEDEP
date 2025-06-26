@echo off
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

set BACKUP_FILE=C:\Users\Pichau\Documents\GitHub\Projeto-CEDEP\sigref\scripts\backup_railway_2025-06-20_12-00.backup
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

REM Limpa apenas as tabelas de agendamento (ordem importa por FK)
echo TRUNCATE TABLE eventos_agendamento_salas CASCADE; TRUNCATE TABLE eventos_agendamento CASCADE; | psql -U %USER% -h %HOST% -p %PORT% -d %DB%

REM Restaura apenas os dados de agendamento e seus relacionamentos
pg_restore -U %USER% -h %HOST% -p %PORT% -d %DB% -v --data-only ^
-t eventos_agendamento ^
-t eventos_agendamento_salas ^
%BACKUP_FILE%

echo Processo concluído.
pause