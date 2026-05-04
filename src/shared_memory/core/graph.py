import json
import os
import sqlite3
import aiosqlite
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from shared_memory.common.utils import get_db_path, log_info, log_error, get_logger, calculate_importance
from shared_memory.common.config import MAX_OBSERVATIONS_PER_ENTITY, GLOBAL_READ_ENTITY_LIMIT

logger = get_logger("graph")

async def get_graph_data(query: str | None = None) -> Dict[str, Any]:
    \"\"\"
    Retrieves knowledge entities and their relations from the SQLite database.
    
    If a query is provided, it performs a search and returns related entities.
    If no query is provided, it returns a limited set of high-importance entities
    to avoid overloading the context.
    \"\"\"
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"entities": [], "relations": [], "observations": []}

    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            entities = []
            relations = []
            observations = []

            # 1. Entity Retrieval
            if query:
                # Search for specific entities
                cursor = await conn.execute(
                    \"\"\"
                    SELECT name, entity_type, description, importance 
                    FROM entities 
                    WHERE (name LIKE ? OR description LIKE ?) 
                    AND status = 'active'
                    LIMIT ?
                    \"\"\",
                    (f"%{query}%", f"%{query}%", GLOBAL_READ_ENTITY_LIMIT)
                )
            else:
                # Default view: High importance active entities
                cursor = await conn.execute(
                    \"\"\"
                    SELECT name, entity_type, description, importance 
                    FROM entities 
                    WHERE status = 'active' 
                    ORDER BY importance DESC 
                    LIMIT ?
                    \"\"\",
                    (GLOBAL_READ_ENTITY_LIMIT,)
                )
            
            entities = [dict(row) for row in await cursor.fetchall()]
            entity_names = [e["name"] for e in entities]

            if not entity_names:
                return {"entities": [], "relations": [], "observations": []}

            # 2. Relation Retrieval
            # Fetch relations where either subject or object is in our entity list
            placeholders = ",".join(["?"] * len(entity_names))
            cursor = await conn.execute(
                f\"\"\"
                SELECT subject, object, predicate 
                FROM relations 
                WHERE (subject IN ({placeholders}) OR object IN ({placeholders})) 
                AND status = 'active'
                \"\"\",
                entity_names + entity_names
            )
            relations = [dict(row) for row in await cursor.fetchall()]

            # 3. Observation Retrieval (Capped per entity)
            # Fetch latest observations for the retrieved entities
            for name in entity_names:
                cursor = await conn.execute(
                    \"\"\"
                    SELECT content, importance, created_at 
                    FROM observations 
                    WHERE entity_name = ? AND status = 'active' 
                    ORDER BY created_at DESC 
                    LIMIT ?
                    \"\"\",
                    (name, MAX_OBSERVATIONS_PER_ENTITY)
                )
                entity_obs = [dict(row) for row in await cursor.fetchall()]
                for obs in entity_obs:
                    obs["entity_name"] = name
                    observations.append(obs)

            return {
                "entities": entities,
                "relations": relations,
                "observations": observations
            }

    except Exception as e:
        log_error("Failed to retrieve graph data", e)
        return {"error": str(e)}

async def save_graph_data(
    entities: List[Dict[str, Any]] | None = None,
    relations: List[Dict[str, Any]] | None = None,
    observations: List[Dict[str, Any]] | None = None
):
    \"\"\"
    Saves new entities, relations, and observations to the database.
    This handles both initial storage and updates.
    \"\"\"
    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as conn:
        now = datetime.now(UTC).isoformat()
        
        # 1. Save Entities
        if entities:
            for entity in entities:
                name = entity.get("name")
                e_type = entity.get("entity_type", "generic")
                desc = entity.get("description", "")
                
                await conn.execute(
                    \"\"\"
                    INSERT INTO entities (name, entity_type, description, status, created_at, updated_at)
                    VALUES (?, ?, ?, 'active', ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        entity_type = excluded.entity_type,
                        description = excluded.description,
                        updated_at = excluded.updated_at
                    \"\"\",
                    (name, e_type, desc, now, now)
                )

        # 2. Save Relations
        if relations:
            for rel in relations:
                sub = rel.get("subject")
                obj = rel.get("object")
                pred = rel.get("predicate", "related_to")
                
                await conn.execute(
                    \"\"\"
                    INSERT INTO relations (subject, object, predicate, status, created_at, updated_at)
                    VALUES (?, ?, ?, 'active', ?, ?)
                    ON CONFLICT(subject, object, predicate) DO UPDATE SET
                        status = 'active',
                        updated_at = excluded.updated_at
                    \"\"\",
                    (sub, obj, pred, now, now)
                )

        # 3. Save Observations
        if observations:
            for obs in observations:
                e_name = obs.get("entity_name")
                content = obs.get("content")
                importance = obs.get("importance", 5)
                
                await conn.execute(
                    \"\"\"
                    INSERT INTO observations (entity_name, content, importance, status, created_at)
                    VALUES (?, ?, ?, 'active', ?)
                    \"\"\",
                    (e_name, content, importance, now)
                )
        
        await conn.commit()
        log_info(f"Saved {len(entities or [])} entities, {len(relations or [])} relations, {len(observations or [])} observations")
