@echo off
setlocal

cd /d "%~dp0.."
set PYTHONPATH=backend

call .venv\Scripts\python.exe -m pytest backend\tests
if errorlevel 1 goto :fail

call .venv\Scripts\python.exe -m mypy --explicit-package-bases backend\app
if errorlevel 1 goto :fail

call .venv\Scripts\python.exe -m ruff check .
if errorlevel 1 goto :fail

if exist frontend\package.json (
    pushd frontend
    call npm run typecheck
    if errorlevel 1 ( popd & goto :fail )
    call npm run lint
    if errorlevel 1 ( popd & goto :fail )
    popd
)

echo All checks passed.
exit /b 0

:fail
echo A check failed.
exit /b 1
