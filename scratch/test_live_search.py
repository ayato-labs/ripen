import asyncio
import json
from ripen.core.search import perform_search
from ripen.infra.database import init_db
from ripen.common.utils import configure_logging

async def test_search():
    configure_logging()
    print("Initializing DB...")
    await init_db()
    
    from ripen.infra.uow import UnitOfWork
    
    query = "Python"
    print(f"Searching for: {query}")
    async with UnitOfWork() as uow:
        results = await perform_search(query, uow)
    
    entities = results[0].get("entities", [])
    print(f"Search Results: Found {len(entities)} entities.")
    for e in entities[:3]:
        print(f" - {e['name']}: {e.get('description', '')[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_search())
