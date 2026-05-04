import json
import asyncio
from typing import Dict, Any, List, Optional
from shared_memory.core.graph import get_graph_data, save_graph_data
from shared_memory.core.bank import read_bank_files
from shared_memory.core.search import perform_search
from shared_memory.common.utils import get_logger, log_info, log_error, mask_sensitive_data
from shared_memory.common.config import MAX_OBSERVATIONS_PER_ENTITY, GLOBAL_READ_ENTITY_LIMIT

logger = get_logger("logic")

async def read_memory_core(query: str | None = None) -> Dict[str, Any]:
    \"\"\"
    The central intelligence for knowledge retrieval.
    Orchestrates search across graph database and memory bank files.
    
    Args:
        query: Optional search term. If None, returns a high-level summary.
    \"\"\"
    log_info(f"Reading memory core with query: {query}")
    
    try:
        # Run graph retrieval and bank retrieval in parallel
        # We use optimized versions that respect global limits
        graph_task = get_graph_data(query)
        bank_task = read_bank_files(query)
        
        # Also perform a hybrid search if query is present
        search_task = perform_search(query) if query else asyncio.sleep(0, result={})

        graph_data, bank_data, search_results = await asyncio.gather(
            graph_task, bank_task, search_task
        )

        # Combine results
        combined = {
            "graph": graph_data,
            "bank": bank_data,
            "search": search_results
        }
        
        # Mask any accidental sensitive data in the response
        json_str = json.dumps(combined)
        masked_json_str = mask_sensitive_data(json_str)
        
        return json.loads(masked_json_str)

    except Exception as e:
        log_error("Failed in read_memory_core", e)
        return {"error": "Internal memory retrieval error"}

async def save_memory_core(
    observations: List[Dict[str, Any]] | None = None,
    entities: List[Dict[str, Any]] | None = None,
    relations: List[Dict[str, Any]] | None = None,
    bank_files: Dict[str, str] | None = None
) -> Dict[str, Any]:
    \"\"\"
    The central intelligence for knowledge storage.
    \"\"\"
    try:
        # 1. Handle Graph updates
        await save_graph_data(entities, relations, observations)
        
        # 2. Handle Bank updates (future implementation)
        if bank_files:
            # For now, we only log bank file update requests
            log_info(f"Bank file updates requested: {list(bank_files.keys())}")
            
        return {"status": "success"}
    except Exception as e:
        log_error("Failed in save_memory_core", e)
        return {"status": "error", "message": str(e)}

async def synthesize_entity_core(entity_name: str) -> Dict[str, Any]:
    \"\"\"
    Retrieves and summarizes everything known about a specific entity.
    \"\"\"
    # This uses get_graph_data specifically for one entity
    data = await get_graph_data(query=entity_name)
    
    # Basic synthesis: count observations
    obs_count = len(data.get("observations", []))
    
    return {
        "entity": entity_name,
        "observation_count": obs_count,
        "details": data
    }

def normalize_llm_args(
    observations: List[str] | None = None,
    entities: List[Dict[str, Any]] | None = None,
    relations: List[List[str]] | None = None,
    entity_name: str | None = None
) -> Dict[str, Any]:
    \"\"\"
    Normalizes inconsistent arguments often provided by LLMs.
    Ensures that structured data matches the internal schema.
    \"\"\"
    normalized_obs = []
    
    # Ensure observations are structured
    if observations:
        for obs in observations:
            if isinstance(obs, str):
                normalized_obs.append({
                    "entity_name": entity_name or "Global",
                    "content": obs,
                    "importance": 5
                })
            elif isinstance(obs, dict):
                normalized_obs.append(obs)

    # Ensure relations are structured list of dicts
    normalized_rels = []
    if relations:
        for rel in relations:
            if isinstance(rel, list) and len(rel) >= 2:
                normalized_rels.append({
                    "subject": rel[0],
                    "object": rel[1],
                    "predicate": rel[2] if len(rel) > 2 else "related_to"
                })
            elif isinstance(rel, dict):
                normalized_rels.append(rel)

    return {
        "observations": normalized_obs,
        "entities": entities,
        "relations": normalized_rels
    }

async def auto_discover_entities(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    \"\"\"
    Analyzes observations to discover new entities that should be created.
    \"\"\"
    entities = []
    existing_entity_names = set()
    
    # We should fetch existing entities here to avoid duplicates
    # For now, we just look at the list of incoming observations
    for obs in observations:
        name = obs.get("entity_name")
        if name and name != "Global" and name not in existing_entity_names:
            entities.append({
                "name": name,
                "entity_type": "implicit",
                "description": "Implicitly created"
            })
            existing_entity_names.add(name)

    # --- Phase 1: Pre-compute AI results ---
    # In a more advanced version, we would use an LLM here to extract 
    # entities from the 'content' of the observations.
    
    return entities
