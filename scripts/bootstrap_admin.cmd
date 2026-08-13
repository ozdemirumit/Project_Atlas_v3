@echo off
setlocal
cd /d "%~dp0.."
set PYTHONPATH=backend
call .venv\Scripts\python.exe -m app.bootstrap
endlocal
