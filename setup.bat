@echo off
setlocal
pushd "%~dp0"

echo ========================================
echo   [Ripen] Environment Setup
echo ========================================
echo.

:: Check for uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 'uv' is not installed or not in PATH.
    echo Please install it first: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

:: Create .venv if it doesn't exist
if not exist .venv (
    echo [Ripen] Creating virtual environment...
    uv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install in editable mode
echo [Ripen] Installing dependencies (including dev and test)...
uv pip install -e .[dev,test]

if %errorlevel% neq 0 (
    echo [ERROR] Installation failed.
    pause
    exit /b 1
)

:: Copy .env.example to .env if not exists
if not exist .env (
    if exist .env.example (
        echo [Ripen] Creating .env file from .env.example...
        copy .env.example .env >nul
    )
)

echo.
echo [Ripen] Setup completed successfully!
echo.

popd
pause
