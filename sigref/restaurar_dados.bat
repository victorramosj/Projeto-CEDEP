@echo off
REM Define a senha do banco novo
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

REM Caminho para o backup filtrado
set BACKUP_FILE=C:\Users\Pichau\Documents\GitHub\Projeto-CEDEP\sigref\backup_railway_2025-06-20_11-15.backup

REM Host, porta e nome do banco
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

REM Truncar tabelas para evitar conflito
echo TRUNCATE TABLE reservas_reserva CASCADE; TRUNCATE TABLE reservas_quarto CASCADE; TRUNCATE TABLE reservas_cama CASCADE; TRUNCATE TABLE reservas_hospede CASCADE; TRUNCATE TABLE reservas_ocupacao CASCADE; | psql -U %USER% -h %HOST% -p %PORT% -d %DB%

echo Processo concluído.
pause
