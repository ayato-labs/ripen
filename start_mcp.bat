@echo off
setlocal
pushd "%~dp0"

echo ========================================
echo   [Ripen] Starting Streamable HTTP MCP Server
echo ========================================
echo.

:: Check for .venv
if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup.bat first to initialize the environment.
    pause
    exit /b 1
)

set PORT=8377
set HOST=127.0.0.1

echo [1] Local Only (127.0.0.1) - Recommended
echo [2] Team/Public (0.0.0.0)  - Accessible from Network
echo.

choice /C 12 /T 3 /D 1 /M "Select mode (auto-default to 1 in 3s):"

if errorlevel 2 (
    set HOST=0.0.0.0
    echo.
    echo Mode: Team/Public
) else (
    set HOST=127.0.0.1
    echo.
    echo Mode: Local Only
)

echo.
echo Starting Ripen Hub (Streamable HTTP) on %HOST%:%PORT%...
echo ----------------------------------------

:: Start server forcing HTTP transport mode
uv run python -m ripen.api.server --http --port %PORT% --host %HOST%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with error code %errorlevel%.
    pause
    exit /b 1
)

popd
pause
