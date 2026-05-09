
import asyncio
import httpx
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def debug_sse_tools():
    url = "http://localhost:8377/sse"
    print(f"Connecting to SSE server at {url}...")
    try:
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                print(f"Number of tools: {len(tools_result.tools)}")
                for tool in tools_result.tools:
                    print(f"Tool: {tool.name}")
                    print(f"  Description: {repr(tool.description)}")
    except Exception as e:
        print(f"Error connecting to SSE server: {e}")

if __name__ == "__main__":
    asyncio.run(debug_sse_tools())
