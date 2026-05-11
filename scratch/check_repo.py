import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from ripen.infra.repository import EmbeddingRepository

async def main():
    repo = EmbeddingRepository(None) # conn can be None for this check
    print(f"Repo: {repo}")
    print(f"Has get_all_embeddings: {hasattr(repo, 'get_all_embeddings')}")
    print(f"Methods: {[m for m in dir(repo) if not m.startswith('_')]}")

if __name__ == "__main__":
    asyncio.run(main())
