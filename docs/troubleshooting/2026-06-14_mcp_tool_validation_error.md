# Troubleshooting: MCP Tool ValidationError (wait_for_previous)

## Symptom
Attempts to call MCP tools (e.g., `save_memory`) from the Gemini CLI result in a `ValidationError`.

Case 1: `wait_for_previous` error
```
ValidationError: 1 validation error for call[save_memory]
wait_for_previous
  Unexpected keyword argument [type=unexpected_keyword_argument, input_value=True, input_type=bool]
```

Case 2: Missing required arguments
```
ValidationError: 3 validation errors for call[save_memory]
entities
  Missing required argument [type=missing_argument, input_value={}, input_type=dict]
...
```

## Cause
1.  **Client Injection**: The client (Gemini CLI) injects a `wait_for_previous` parameter into tool invocation payloads.
2.  **Partial Payloads**: Some clients or subagents may send incomplete payloads missing `entities`, `relations`, or `observations`. The server's `fastmcp` implementation uses strict Pydantic validation, which rejects both unexpected and missing required arguments.

## Solution
1.  **Compatibility Argument**: Updated tool signatures to include `wait_for_previous: bool | None = None`.
2.  **Optional Parameters**: Updated `save_memory` signature to make `entities`, `relations`, and `observations` optional by providing default empty lists (`[]`).

## Status
Resolved via ADR-0008 and subsequent robustness updates. Applied to `src/ripen/api/server.py` and `src/ripen/api/admin_server.py`.
