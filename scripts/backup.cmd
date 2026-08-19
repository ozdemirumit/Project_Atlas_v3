@echo off
setlocal
cd /d "%~dp0.."

if not exist backups mkdir backups

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "stamp=%%I"
set "outfile=backups\atlas3_%stamp%.dump"
set "url=%ATLAS_DATABASE_URL%"
if "%url%"=="" set "url=postgresql+psycopg://atlas3:atlas3@localhost:5432/atlas3"
set "url=%url:postgresql+psycopg://=postgresql://%"

echo Backing up %url% to %outfile% ...
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" --format=custom --file="%outfile%" --dbname="%url%"
if errorlevel 1 (
    echo Backup FAILED.
    exit /b 1
)
echo Backup complete: %outfile%
endlocal
