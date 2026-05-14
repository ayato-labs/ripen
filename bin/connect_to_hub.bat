@echo off
setlocal
pushd "%~dp0.."

echo.
echo [Ripen Client] Connect to Remote Team Hub
echo ----------------------------------------

set /p HUB_URL="Enter Hub URL (default: http://localhost:8377): "

if "%HUB_URL%"=="" (
    set HUB_URL=http://localhost:8377
)

echo.
echo Connecting to %HUB_URL% via Stdio Proxy...
echo.

uv run ripen --stdio --hub-url %HUB_URL%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Proxy connection failed.
    pause
)
popd
