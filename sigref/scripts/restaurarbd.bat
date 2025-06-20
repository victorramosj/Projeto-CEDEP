@echo off
REM Define a senha do PostgreSQL
set PGPASSWORD=vDadjhfHsAXBQkxbEkskxbOZSRhogYvs

REM Configurações do Banco de Dados
set HOST=mainline.proxy.rlwy.net
set PORT=32588
set DB=railway
set USER=postgres

echo Conectando ao banco de dados '%DB%' para apagar todos os dados...

REM Tabela de system catalog para listar todas as tabelas
REM Isso é um pouco avançado, mas pode ajudar a identificar todas as tabelas
REM SELECT tablename FROM pg_tables WHERE schemaname = 'public';

REM LISTA MANUAL DAS SUAS TABELAS:
REM Substitua esta lista pelas tabelas reais do seu banco, na ordem correta,
REM ou use TRUNCATE ... CASCADE para a maioria dos casos.
REM Para obter a lista de suas tabelas, você pode usar `\dt` no psql.
REM Cuidado com a ordem se não usar CASCADE! Tabelas referenciadas por FK devem ser truncadas antes.
set "TABLES_TO_TRUNCATE=eventos_agendamento_salas, eventos_agendamento, reservas_reserva, hospedes_hospede, monitoramento_registro, problemas_problema, auth_user, auth_group, auth_permission, django_admin_log, django_content_type, django_migrations, django_session, authtoken_token"

echo TRUNCATE TABLE %TABLES_TO_TRUNCATE% CASCADE; | psql -U %USER% -h %HOST% -p %PORT% -d %DB% -w

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Falha ao apagar os dados do banco!
    echo Verifique se as tabelas listadas existem e se o usuario tem permissoes.
) ELSE (
    echo.
    echo Todos os dados do banco de dados '%DB%' foram apagados com sucesso!
    echo As tabelas permanecem vazias.
)

echo.
pause