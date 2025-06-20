@echo off
set PGPASSWORD=HKhnFzXggtmylfsSKcPbVGfQEvataqYo

for /f %%i in ('wmic OS Get localdatetime ^| find "."') do set datetime=%%i
set datetime=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

pg_dump -U postgres -h shortline.proxy.rlwy.net -p 13741 -d railway -F c -b -v -f backup_railway_%datetime%.backup

echo Backup concluído: backup_railway_%datetime%.backup
pause
