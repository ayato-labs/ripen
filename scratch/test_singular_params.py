import asyncio
from fastmcp import FastMCP

mcp = FastMCP("Test")

@mcp.tool()
async def save_memory(
    entities: list[dict] | None = None,
    relations: list[dict] | None = None,
    observations: list[dict] | None = None,
    entity: dict | list[dict] | None = None,
    relation: dict | list[dict] | None = None,
    observation: dict | list[dict] | None = None,
    bank_files: list[str] | None = None,
    agent_id: str | None = None,
    wait_for_previous: bool | None = None,
) -> str:
    entities = entities or []
    relations = relations or []
    observations = observations or []

    if entity:
        if isinstance(entity, list):
            entities.extend(entity)
        else:
            entities.append(entity)

    if relation:
        if isinstance(relation, list):
            relations.extend(relation)
        else:
            relations.append(relation)

    if observation:
        if isinstance(observation, list):
            observations.extend(observation)
        else:
            observations.append(observation)

    return f"ok: entities={entities}, relations={relations}, observations={observations}"

async def main():
    try:
        # Simulate a call with singular 'entity'
        res = await mcp.call_tool("save_memory", {
            "entity": {"name": "TestEntity", "entity_type": "concept", "description": "desc"},
            "wait_for_previous": True
        })
        print(f"Success singular: {res}")
        
        # Simulate a call with plural 'entities'
        res2 = await mcp.call_tool("save_memory", {
            "entities": [{"name": "PluralEntity", "entity_type": "concept"}],
        })
        print(f"Success plural: {res2}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
