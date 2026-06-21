@echo off
setlocal
pushd "%~dp0"

echo ========================================
echo   [Ripen] Environment Setup
echo ========================================
echo.

where uv >nul 2>&1
if errorlevel 1 goto ERR_NO_UV

if exist .venv goto VENV_EXISTS
echo [Ripen] Creating virtual environment...
uv venv
if errorlevel 1 goto ERR_VENV

:VENV_EXISTS
echo [Ripen] Installing dependencies (including dev and test)...
uv pip install -e .[dev,test]
if errorlevel 1 goto ERR_INSTALL

if exist .env goto ENV_EXISTS
if not exist .env.example goto ENV_EXISTS
echo [Ripen] Creating .env file from .env.example...
copy .env.example .env >nul

:ENV_EXISTS
echo.
echo [Ripen] Setup completed successfully!
echo.
popd
pause
exit /b 0

:ERR_NO_UV
echo [ERROR] 'uv' is not installed or not in PATH.
echo Please install it first: https://github.com/astral-sh/uv
pause
popd
exit /b 1

:ERR_VENV
echo [ERROR] Failed to create virtual environment.
pause
popd
exit /b 1

:ERR_INSTALL
echo [ERROR] Installation failed.
pause
popd
exit /b 1
