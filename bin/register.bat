@echo off
pushd "%~dp0.."
echo Registering Ripen with IDEs...
uv run shared-memory-register
pause
popd
