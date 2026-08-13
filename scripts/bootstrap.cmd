@echo off
setlocal

cd /d "%~dp0.."

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -e .[dev]

if not exist .env (
    copy .env.example .env >nul
    echo Created .env from .env.example — review it before running dev.cmd.
)

if exist frontend\package.json (
    where npm >nul 2>nul
    if %ERRORLEVEL%==0 (
        pushd frontend
        call npm install
        popd
    ) else (
        echo npm was not found on PATH — install Node.js 20+ before running the frontend.
    )
)

echo Bootstrap complete.
endlocal
