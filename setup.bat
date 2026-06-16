@echo off
setlocal
pushd "%~dp0"

echo [Ripen] Starting environment setup...
echo ----------------------------------------

:: Check for uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] 'uv' is not installed or not in PATH.
    echo Please install it first: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

:: Create .venv if it doesn't exist
if not exist .venv (
    echo [Ripen] Creating virtual environment...
    uv venv
    if %errorlevel% neq 0 (
        echo [Error] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install in editable mode
echo [Ripen] Installing dependencies in editable mode (uv pip install -e .)...
uv pip install -e .

if %errorlevel% neq 0 (
    echo [Error] Installation failed.
    pause
    exit /b 1
)

echo.
echo [Ripen] Setup completed successfully!
echo You can now start the system using start.bat.
echo.

popd
pause
