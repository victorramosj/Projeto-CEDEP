@echo off
REM Define a senha do PostgreSQL
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

REM Configurações do Banco de Dados
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

REM Caminho para o seu arquivo de backup COMPLETO
set BACKUP_FILE=C:\Users\Pichau\Documents\GitHub\Projeto-CEDEP\sigref\scripts\railway_backup_2025-06-20_17-18.sqlc

echo Restaurando apenas os dados no banco '%DB%'...

pg_restore -Fc --data-only -h %HOST% -p %PORT% -U %USER% -d %DB% "%BACKUP_FILE%"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: A restauracao dos dados falhou!
    echo Verifique se o arquivo de backup existe e as permissoes.
) ELSE (
    echo.
    echo Restauracao dos dados concluida com sucesso!
)

echo.
pause