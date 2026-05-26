import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath("src"))

from ripen.core import logic

async def main():
    entities = [
        {
            "name": "Docker Discontinuation",
            "entity_type": "decision",
            "description": "The policy to distribute Docker container images was discontinued in favor of Windows .exe native binaries."
        },
        {
            "name": "Ripen",
            "entity_type": "software",
            "description": "Streamable HTTP/SSE MCP memory server."
        }
    ]
    relations = [
        {
            "source": "Docker Discontinuation",
            "target": "Ripen",
            "predicate": "applied_to"
        }
    ]
    observations = [
        {
            "entity_name": "Docker Discontinuation",
            "content": "Docker image distribution was removed due to corporate licensing issues with Docker Desktop. Since Ripen only requires a single Windows environment to serve the entire team via HTTP/SSE, cross-platform compatibility is practically complete without needing complex containerization."
        },
        {
            "entity_name": "Docker Discontinuation",
            "content": "CI/CD has been simplified to build and release Windows .exe binaries only."
        }
    ]
    
    print("Saving memory to Ripen local database...")
    result = await logic.save_memory_core(
        entities=entities,
        relations=relations,
        observations=observations,
        agent_id="ayato-labs"
    )
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
