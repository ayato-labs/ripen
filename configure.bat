@echo off
setlocal
pushd "%~dp0"

echo ========================================
echo   [Ripen] Settings Configuration
echo ========================================
echo.

if not exist .venv goto ERR_NO_VENV

.venv\Scripts\python -m ripen.cli.init
if errorlevel 1 goto ERR_CONFIG

popd
exit /b 0

:ERR_NO_VENV
echo [ERROR] Virtual environment (.venv) not found.
echo Please run setup.bat first to initialize the environment.
pause
popd
exit /b 1

:ERR_CONFIG
echo.
echo [ERROR] Configuration wizard exited with error code %errorlevel%.
pause
popd
exit /b 1
