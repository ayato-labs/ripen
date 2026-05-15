
import sys
import os
import json
import asyncio
import httpx
import time
from pathlib import Path

# Absolute log for emergency diagnostics
LOG_PATH = Path(r"C:\Users\saiha\My_Service\programing\MCP\Ripen\Ripen-free\logs\proxy_emergency.log")

def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} | {msg}\n")
    except Exception as e:
        # Fallback to stderr if file logging fails, adhering to 'no except: pass' rule
        sys.stderr.write(f"PROXY_LOG_ERROR: {e} | msg: {msg}\n")

async def run_stdio_proxy(hub_url: str | None = None):
    """
    Acts as a bridge between STDIO-only agents and the SSE Ripen Hub.
    If hub_url is not provided, defaults to local hub.
    """
    log(f"=== PROXY START (hub_url={hub_url}) ===")
    
    if not hub_url:
        hub_url = "http://127.0.0.1:8377"
    
    # Ensure no trailing slash for consistent path joining
    hub_url = hub_url.rstrip("/")
    
    async with httpx.AsyncClient(timeout=None) as client:
        # Check Hub availability using a streaming request to avoid hanging on infinite SSE streams
        try:
            async with client.stream("GET", f"{hub_url}/sse") as response:
                if response.status_code != 200:
                    log(f"Hub error: {response.status_code}")
                    sys.exit(1)
                log("Hub connection verified (Headers received).")
                # We don't need to read the body here, we just verified the endpoint exists
        except Exception as e:
            log(f"Hub unreachable: {e}")
            sys.exit(1) # Signal failure for server.py fallback

        from mcp.client.sse import sse_client
        async with sse_client(f"{hub_url}/sse") as (read_stream, write_stream):
            log("SSE Linked.")
            
            async def to_ide():
                try:
                    async for message in read_stream:
                        if isinstance(message, Exception):
                            log(f"Stream error: {message}")
                            break
                        data = message.message.model_dump_json(by_alias=True, exclude_none=True)
                        sys.stdout.write(data + "\n")
                        sys.stdout.flush()
                except Exception as e:
                    log(f"to_ide crash: {e}")
            
            async def from_ide():
                while True:
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line: break
                    try:
                        data = json.loads(line)
                        from mcp.types import JSONRPCMessage
                        from mcp.shared.session import SessionMessage
                        msg = JSONRPCMessage.model_validate(data)
                        await write_stream.send(SessionMessage(message=msg))
                    except Exception as e:
                        log(f"IDE Parse Error: {e}")

            await asyncio.gather(to_ide(), from_ide())

if __name__ == "__main__":
    try:
        asyncio.run(run_stdio_proxy())
    except SystemExit:
        # Expected if hub is missing
        sys.exit(1)
    except Exception as e:
        log(f"PROXY FATAL: {e}")
        sys.exit(1)
