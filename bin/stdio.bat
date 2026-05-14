@echo off
pushd "%~dp0.."
echo.
echo [Ripen Hub] Starting Local Stdio Server...
echo ----------------------------------------
echo Communication: Standard I/O (STDIO)
echo Use this mode for direct MCP integration.
echo.

uv run ripen --stdio

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server exited with code %ERRORLEVEL%
    pause
)
popd
