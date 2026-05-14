@echo off
pushd "%~dp0.."
echo.
echo [Ripen Admin] Starting Admin Control Plane...
echo ----------------------------------------
echo This server provides advanced maintenance and diagnostic tools.
echo.

uv run ripen-admin-server

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Admin server exited with code %ERRORLEVEL%
    pause
)
popd
