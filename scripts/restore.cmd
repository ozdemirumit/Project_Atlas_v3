@echo off
setlocal
cd /d "%~dp0.."

if "%~1"=="" (
    echo Usage: scripts\restore.cmd backups\atlas3_YYYYMMDD_HHMMSS.dump
    exit /b 1
)

if "%ATLAS_DATABASE_URL%"=="" set "ATLAS_DATABASE_URL=postgresql+psycopg://atlas3:atlas3@localhost:5432/atlas3"

echo Restoring %~1 into %ATLAS_DATABASE_URL% (existing objects are dropped and recreated) ...
"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" --clean --if-exists --dbname="%ATLAS_DATABASE_URL:postgresql+psycopg://=postgresql://%" "%~1"
if errorlevel 1 (
    echo Restore FAILED.
    exit /b 1
)
echo Restore complete.
endlocal
