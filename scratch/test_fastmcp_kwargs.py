import asyncio
from fastmcp import FastMCP
import pydantic

mcp = FastMCP("Test")

@mcp.tool()
async def save_memory(
    entities: list,
    **kwargs
) -> str:
    return "ok"

async def main():
    # Simulate a call tool request
    try:
        res = await mcp.call_tool("save_memory", {"entities": [], "wait_for_previous": True})
        print(f"Success: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())