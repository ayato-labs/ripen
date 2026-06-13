import asyncio
from fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("Test")

class SaveMemoryInput(BaseModel):
    entities: list = Field(default_factory=list)

    class Config:
        extra = 'ignore'

@mcp.tool()
async def save_memory(
    input_data: SaveMemoryInput
) -> str:
    return "ok"

async def main():
    # Simulate a call tool request
    try:
        res = await mcp.call_tool("save_memory", {"input_data": {"entities": [], "wait_for_previous": True}})
        print(f"Success: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())