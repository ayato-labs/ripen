@echo off
setlocal
pushd "%~dp0"

echo ========================================
echo   [Ripen] Settings Configuration
echo ========================================
echo.

:: Check for .venv
if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup.bat first to initialize the environment.
    pause
    exit /b 1
)

:: Run settings wizard
uv run python -m ripen.cli.init

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Configuration wizard exited with error code %errorlevel%.
    pause
    exit /b 1
)

popd
pause
