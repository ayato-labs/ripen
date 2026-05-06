import asyncio
from fastmcp import FastMCP
from shared_memory.api.server import _patched_http_app

async def debug_middleware():
    mcp = FastMCP("SharedMemoryServer")
    # Manually call our patch or the patched method
    app = mcp.http_app()
    print("Middleware stack:")
    for middleware in app.user_middleware:
        print(f" - {middleware.cls}")

if __name__ == "__main__":
    asyncio.run(debug_middleware())
