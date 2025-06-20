@echo off
REM Define a senha do PostgreSQL
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

REM Define o nome do arquivo de backup com timestamp
for /f "tokens=1-4 delims=/ " %%i in ('date /t') do (set DT=%%k-%%j-%%i)
for /f "tokens=1-2 delims=: " %%i in ('time /t') do (set TM=%%i-%%j)
set BACKUP_FILE_NAME=railway_backup_%DT%_%TM%.sqlc
set BACKUP_PATH=C:\Users\Pichau\Documents\GitHub\Projeto-CEDEP\sigref\scripts
set FULL_BACKUP_PATH=%BACKUP_PATH%\%BACKUP_FILE_NAME%

REM Configurações do Banco de Dados
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

echo Iniciando backup completo do banco de dados '%DB%'...

REM Cria a pasta de backups se não existir
if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"

REM Executa o pg_dump para criar o backup completo
pg_dump -Fc -h %HOST% -p %PORT% -U %USER% -d %DB% -f "%FULL_BACKUP_PATH%"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: O backup falhou! Verifique as configurações e a conexão.
) ELSE (
    echo.
    echo Backup completo do banco de dados '%DB%' concluido com sucesso em:
    echo %FULL_BACKUP_PATH%
)

echo.
pause