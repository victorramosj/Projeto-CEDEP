@echo off
REM Define a senha do banco novo
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

REM Caminho para o backup antigo
set BACKUP_FILE=C:\Users\Pichau\Documents\GitHub\Projeto-CEDEP\cedepe\backup_railway_2025-06-20_10-43.backup

REM Caminho para salvar o dump atual antes do restore
set PRE_RESTORE_BACKUP=railway_pre_restore.backup

REM Host, porta e nome do banco
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

echo Criando backup atual antes de restaurar...
pg_dump -U %USER% -h %HOST% -p %PORT% -d %DB% -F c -v -f %PRE_RESTORE_BACKUP%

echo Restaurando dados do backup antigo...
pg_restore -U %USER% -h %HOST% -p %PORT% -d %DB% --data-only -v "%BACKUP_FILE%"

echo Processo concluído.
pause
