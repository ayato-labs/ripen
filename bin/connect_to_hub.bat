@echo off
setlocal
pushd "%~dp0.."

echo ========================================
echo   [Ripen] Connect to Remote Team Hub
echo ========================================
echo.

if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup.bat in the root folder first.
    pause
    exit /b 1
)

set /p HUB_URL="Enter Hub URL (default: http://localhost:8377): "

if "%HUB_URL%"=="" (
    set HUB_URL=http://localhost:8377
)

echo.
echo Connecting to %HUB_URL% via Stdio Proxy...
echo ----------------------------------------

uv run python -m ripen.api.server --stdio --hub-url %HUB_URL%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Proxy connection failed.
    pause
)

popd
