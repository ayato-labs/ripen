@echo off
setlocal
pushd "%~dp0.."

echo ========================================
echo   [Ripen] Running Test Suite
echo ========================================
echo.

if not exist .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup.bat in the root folder first.
    pause
    exit /b 1
)

uv run pytest tests -v

pause
popd
