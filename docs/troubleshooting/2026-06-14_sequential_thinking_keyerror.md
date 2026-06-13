# Troubleshooting: Sequential Thinking KeyError ('thought_number')

## Symptom
`sequential_thinking` tools fail during the final distillation phase with the following error:
```
ERROR | ripen.core.thought_logic:process_thought_core:244 - Final distillation failed for session default_session: 'thought_number'
```
This is a `KeyError` indicating that the key `thought_number` was missing or inaccessible in a thought history item.

## Cause
1.  **Inconsistent types**: Items in `thought_history` could be `aiosqlite.Row` objects (which require bracket access) or dictionaries. If the distillation logic expected a dictionary but received a Row object (or vice versa in some edge cases), access might fail depending on the implementation.
2.  **Missing key in manual construction**: In `process_thought_core`, the final thought was being appended as `{"thought": masked_thought}`, which lacked the `thought_number` key required by `auto_distill_knowledge`.

## Solution
1.  **Defensive Access**: Updated `src/ripen/core/distiller.py` to use `.get()` for dictionaries and `getattr()` for other objects when accessing `thought_number` and `thought`.
2.  **Explicit Conversion & Completion**: Updated `src/ripen/core/thought_logic.py` to:
    -   Explicitly convert all history items to dictionaries.
    -   Include `thought_number` in the dictionary for the final thought being passed to the distiller.

## Status
Resolved on 2026-06-14.
- `src/ripen/core/distiller.py`: Modified
- `src/ripen/core/thought_logic.py`: Modified
