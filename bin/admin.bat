@echo off
pushd "%~dp0.."
echo Starting Ripen Admin Dashboard...
uv run shared-memory-admin-server
popd
