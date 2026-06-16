@echo off
setlocal
pushd "%~dp0"

:: Check for .venv
if not exist .venv (
    echo [Error] Virtual environment (.venv) not found.
    echo Please run setup.bat first to initialize the environment.
    pause
    exit /b 1
)

echo [Ripen] Starting Hub Server...
echo ----------------------------------------

:: Use uv run to launch the main entry point
uv run ripen

if %errorlevel% neq 0 (
    echo.
    echo [Error] System exited with error code %errorlevel%.
    pause
    exit /b 1
)

popd
pause
