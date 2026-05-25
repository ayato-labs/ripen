# ADR-0005: Model Customization, Cache Coexistence, and Automatic Embedding Migration

- **Date**: 2026-05-25
- **Status**: Proposed
- **Deciders**: ayato-labs (User), Antigravity (Agent)

## Context
When the user switches the embedding engine or model (e.g. from `fastembed` to `models/gemini-embedding-2`), two key issues arise under the current design:
1. **Cache Overwrite**: The `embedding_cache` table uses `content_hash` as its single `PRIMARY KEY`. Switching models causes the cache query to miss, compute new embeddings, and overwrite the existing cache entry using `INSERT OR REPLACE`. If the user switches back, the old model's cache is lost.
2. **Dimension Mismatches**: Stored vectors in the `embeddings` table are not automatically updated. This leads to dimension mismatches during hybrid search when query embeddings are generated using the new model, causing search crashes.

We need to enable coexistence of cache values for multiple models and build an automatic background/startup migration system to re-calculate embeddings when model changes are detected.

## Decision
1. **Cache Coexistence via Composite Primary Key**:
   - Migrate the `embedding_cache` table to use a composite primary key: `PRIMARY KEY (content_hash, model_name)`.
   - Implement an SQLite schema migration to transition the table safely.
2. **Automatic Re-embedding Migration**:
   - On system startup (`init_db`), check if there are active embeddings in the database that were computed with a model different from the current `settings.embedding_model`.
   - If a mismatch is detected, run an automatic batch re-calculation:
     - Fetch the original text contents of affected active entities and bank files.
     - Compute new embeddings in batches (utilizing the updated `embedding_cache` if available to prevent redundant API calls).
     - Upsert the new vectors into the `embeddings` table with the current `model_name`.
3. **Setup Wizard Warning & Prompts**:
   - Prompt user during the setup wizard for engine/model configuration and show clear warnings about potential re-calculation overheads.

## Consequences
### Positive
- Zero search downtime or crashes from dimension mismatches after configuring a new model.
- Switching back and forth between models (e.g. local testing with `fastembed` and production cloud run with `gemini-embedding-2`) does not incur repeated API billing costs since cache entries coexist.
- Automated recovery preserves data integrity without requiring manual database cleaning.

### Negative / Risks
- Re-calculating all active entity and file embeddings on model switch can take time and trigger API rate-limits if the database contains thousands of entries. We must compute in batches and implement rate-limit handling.
- Increased disk space usage in `knowledge.db` since multiple models' vectors are kept in the cache.

## References
- Issue: #174
