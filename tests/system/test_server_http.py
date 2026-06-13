import os
import shutil
import signal
import subprocess
import sys
import time

import httpx
import pytest


def _prepare_test_env(test_dir: str) -> dict:
    """Sets up the environment variables and directories for the test server."""
    env = os.environ.copy()
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = src_path

    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(os.path.join(test_dir, "bank"), exist_ok=True)
    env["MEMORY_DB_PATH"] = os.path.join(test_dir, "knowledge.db")
    env["THOUGHTS_DB_PATH"] = os.path.join(test_dir, "thoughts.db")
    env["MEMORY_BANK_DIR"] = os.path.join(test_dir, "bank")
    return env


def _stop_server_process(process: subprocess.Popen):
    """Gracefully stops the server process."""
    if process.poll() is None:
        if sys.platform == "win32":
            process.terminate()
        else:
            process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="module")
def server_process():
    """Starts the Ripen Hub server in a background process."""
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_db"))
    env = _prepare_test_env(test_dir)

    log_file_path = os.path.join(test_dir, "server.log")
    log_file = open(log_file_path, "w", encoding="utf-8")

    process = subprocess.Popen(
        [sys.executable, "-m", "ripen.api.server", "--port", "8377"],
        stdout=log_file,
        stderr=log_file,
        text=True,
        env=env
    )

    max_retries = 60
    retry_interval = 1
    server_ready = False

    for _attempt in range(max_retries):
        if process.poll() is not None:
            log_file.close()
            with open(log_file_path, encoding="utf-8") as f:
                logs = f.read()
            msg = f"Server died unexpectedly (code {process.returncode}). Logs:\n{logs}"
            pytest.fail(msg)

        try:
            # Increased timeout to 2s for slow CI
            response = httpx.get("http://localhost:8377/dashboard/", timeout=2.0)
            if response.status_code in [200, 307, 401, 404]:
                server_ready = True
                break
        except Exception:
            if _attempt % 10 == 0:
                print(f"Attempt {_attempt}: Waiting for server to be ready...")
            time.sleep(retry_interval)

    if not server_ready:
        log_file.close()
        with open(log_file_path, encoding="utf-8") as f:
            logs = f.read()
        msg = f"Server failed to start after {max_retries} seconds. Logs:\n{logs}"
        pytest.fail(msg)

    yield process

    _stop_server_process(process)
    log_file.close()

    if os.path.exists(log_file_path):
        with open(log_file_path, encoding="utf-8") as f:
            print(f"\n--- Server Logs ---\n{f.read()}\n-------------------")

    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.mark.asyncio
@pytest.mark.system
async def test_server_http_connectivity(server_process):
    """
    System Test: サーバーが起動し、HTTPリクエストを受け付けることを検証。
    """
    assert server_process.poll() is None, "Server process died before test started"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8377/dashboard/", timeout=5.0)
            assert response.status_code in [200, 307, 401, 404]
        except httpx.ConnectError:
            pytest.fail("Failed to connect to the server on port 8377 for dashboard")

        try:
            response = await client.post(
                "http://localhost:8377/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "1.0"}
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                timeout=5.0
            )
            assert response.status_code in [200, 406]
        except httpx.ConnectError:
            pytest.fail("Failed to connect to the server on port 8377 for MCP request")
        except Exception as e:
            pytest.fail(f"MCP Request failed with unexpected error: {e}")
