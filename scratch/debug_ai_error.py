import asyncio
import os
import json
from unittest.mock import MagicMock, patch

# Mock settings before importing anything that uses them
os.environ["SHARED_MEMORY_HOME"] = "debug_data"
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["EMBEDDING_ENGINE"] = "gemini"

from shared_memory.core import logic
from shared_memory.infra.database import init_db

async def debug_ai_error():
    await init_db(force=True)
    
    fake_client = MagicMock()
    # Simulate failure
    fake_client.aio.models.embed_content.side_effect = Exception("AI Down")
    
    print("Patching get_gemini_client...")
    with patch("shared_memory.infra.embeddings.get_gemini_client", return_value=fake_client):
        print("Calling save_memory_core...")
        result = await logic.save_memory_core(entities=["ErrorEntity"])
        print(f"RESULT: {result}")
        if "AI Error" in result:
            print("SUCCESS: Got expected AI Error")
        else:
            print("FAILURE: Did not get AI Error")

if __name__ == "__main__":
    asyncio.run(debug_ai_error())
