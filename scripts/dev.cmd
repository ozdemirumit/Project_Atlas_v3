@echo off
setlocal

cd /d "%~dp0.."

where docker >nul 2>nul
if %ERRORLEVEL%==0 (
    docker compose up -d postgres
) else (
    echo docker was not found on PATH — start PostgreSQL 18 yourself and set ATLAS_DATABASE_URL.
)

set PYTHONPATH=backend
call .venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head

start "Atlas API" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000"

if exist frontend\package.json (
    start "Atlas Web" cmd /k "cd frontend && npm run dev"
)

echo Web Workspace Shell:            http://localhost:5173
echo Interactive API Documentation:  http://localhost:8000/docs
echo System Health Endpoint:         http://localhost:8000/api/health
endlocal
