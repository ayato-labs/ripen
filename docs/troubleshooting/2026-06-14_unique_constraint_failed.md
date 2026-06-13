# Troubleshooting: UNIQUE constraint failed (thought_history)

## Symptom
`sequential_thinking` fails with a critical database error:
```
sqlite3.IntegrityError: UNIQUE constraint failed: thought_history.session_id, thought_history.thought_number
```
This error bubbles up through the `process_thought_core` function, ultimately throwing a `DatabaseError` to the MCP client.

## Cause
The database table `thought_history` enforces a primary key on `(session_id, thought_number)`. 
In `src/ripen/core/thought_logic.py`, the validation logic previously skipped checking for duplicate `thought_number`s if `is_revision=True`. If an AI agent incorrectly attempted a revision by reusing an existing `thought_number` (e.g., trying to overwrite step 3 by sending `thought_number=3`), the application logic allowed it through, resulting in the database enforcing the unique constraint and crashing the request.

## Solution
Modified `_validate_and_insert_thought` in `src/ripen/core/thought_logic.py` to enforce the uniqueness of `thought_number` *regardless* of the `is_revision` flag. 

If a duplicate `thought_number` is provided, the application now intercepts it and gracefully returns a structured error dictionary:
```json
{
  "error": "Duplicate thought number: #X already exists... Please use a new, unique thought_number even for revisions.",
  "thoughtNumber": X,
  "totalThoughts": Y
}
```
This allows the AI agent to receive the error context cleanly and retry with a valid `thought_number`, preventing the database crash.

## Status
Resolved on 2026-06-14. Applied to `src/ripen/core/thought_logic.py`.