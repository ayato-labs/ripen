
import asyncio
import json
from shared_memory.api.server import mcp

async def debug_raw_tools():
    tools = await mcp.list_tools()
    for tool in tools:
        print(f"Tool: {tool.name}")
        # Convert to standard MCP tool
        mcp_tool = tool.to_mcp_tool()
        print(f"  MCP Tool Name: {mcp_tool.name}")
        print(f"  MCP Tool Description: {repr(mcp_tool.description)}")

if __name__ == "__main__":
    asyncio.run(debug_raw_tools())
