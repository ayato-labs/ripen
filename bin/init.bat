@echo off
setlocal
pushd "%~dp0.."

echo ========================================
echo   [Ripen] Setup / Re-configure Wizard
echo ========================================
echo.

if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup.bat in the root folder first.
    pause
    exit /b 1
)

:: Run the interactive initialization CLI
uv run python -m ripen.cli.init

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup exited with error code %errorlevel%.
    pause
    exit /b 1
)

echo.
echo [Ripen] Configuration completed!
pause
popd
