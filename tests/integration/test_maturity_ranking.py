
import pytest

from ripen.cli.salvage import salvage_related_knowledge
from ripen.core.logic import save_memory_core, save_troubleshooting_knowledge_core
from ripen.core.search import perform_keyword_search, perform_search
from ripen.core.thought_logic import process_thought_core
from ripen.infra.database import init_db


@pytest.mark.asyncio
async def test_maturity_ranking_logic():
    await init_db(force=True)
    
    keyword = "optimization"
    
    # 1. Save STABLE knowledge (Entity)
    await save_memory_core(
        entities=[{"name": "OptimizationEngine", "description": "A stable system for optimization tasks."}],
        agent_id="test_user"
    )
    
    # 2. Save OBSERVED knowledge (Bank File)
    await save_memory_core(
        bank_files={"optimization_notes.md": "Observed notes about optimization strategies."},
        agent_id="test_user"
    )
    
    # 3. Save TRANSIENT knowledge (Thought History)
    await process_thought_core(
        thought="I am thinking about optimization for this specific session.",
        thought_number=1,
        total_thoughts=1,
        next_thought_needed=False,
        session_id="session-123",
        agent_id="test_user"
    )
    
    # 4. Save PREMIUM STABLE knowledge (Troubleshooting)
    await save_troubleshooting_knowledge_core(
        title="Optimization Failure Fix",
        solution="Fixed the optimization failure by increasing memory limit.",
        affected_functions=["run_opt"]
    )
    
    # --- VERIFICATION 1: Keyword Search Order ---
    results = await perform_keyword_search(keyword, limit=10)
    sources = [r["source"] for r in results]
    
    # troubleshooting should be high due to 2.5 boost
    # entities should be next (1.5 boost)
    # bank_files next (1.0 boost)
    # thought_history lowest (0.3 boost)
    
    print(f"\nKeyword search results: {sources}")
    assert "troubleshooting" in sources
    assert "entities" in sources
    assert "bank_files" in sources
    assert "thought_history" in sources
    
    # Verify order (roughly)
    ts_idx = sources.index("troubleshooting")
    th_idx = sources.index("thought_history")
    assert ts_idx < th_idx, "Troubleshooting should be ranked higher than Thought History"

    # --- VERIFICATION 2: Hybrid Search Maturity Boosting ---
    graph_data, bank_data = await perform_search(keyword, limit=5)
    # Search returns graph data, we check if troubleshooting is included
    assert len(graph_data["troubleshooting"]) > 0
    assert graph_data["troubleshooting"][0]["title"] == "Optimization Failure Fix"

    # --- VERIFICATION 3: Salvage Exclusion ---
    salvage_results = await salvage_related_knowledge(keyword, "test-session")
    salvage_types = [r["type"] for r in salvage_results]
    
    print(f"Salvage results: {salvage_types}")
    assert "troubleshooting" in salvage_types
    assert "entity" in salvage_types
    assert "bank_file" in salvage_types
    # TRANSIENT should be EXCLUDED
    for res in salvage_results:
        assert res["type"] != "thought_history"
        assert "thinking about optimization" not in res["content"]

    print("\nMaturity ranking verification PASSED")
