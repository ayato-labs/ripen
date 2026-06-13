import asyncio
from fastmcp import FastMCP

mcp = FastMCP("Test")

@mcp.tool()
async def save_memory(
    entities: list[dict],
    relations: list[dict],
    observations: list[dict],
    wait_for_previous: bool | None = None,
) -> str:
    return "ok"

async def main():
    try:
        # Simulate missing arguments
        res = await mcp.call_tool("save_memory", {"entities": [], "wait_for_previous": True})
        print(f"Success: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())