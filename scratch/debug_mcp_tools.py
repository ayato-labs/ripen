
import asyncio
import json
from shared_memory.api.server import mcp

async def debug_tools():
    print(f"Server name: {mcp.name}")
    # FastMCP doesn't have a simple list of tool objects in the way I expected
    # Let's use its own list_tools logic
    tools = await mcp.list_tools()
    print(f"Number of tools: {len(tools)}")
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")

if __name__ == "__main__":
    asyncio.run(debug_tools())
