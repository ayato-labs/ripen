# Troubleshooting: MCP Tool ValidationError (wait_for_previous)

## Symptom
Attempts to call MCP tools (e.g., `save_memory`) from the Gemini CLI result in a `ValidationError` related to `wait_for_previous`.
```
ValidationError: 1 validation error for call[save_memory]
wait_for_previous
  Unexpected keyword argument [type=unexpected_keyword_argument, input_value=True, input_type=bool]
```

## Cause
The client (Gemini CLI) injects a `wait_for_previous` parameter into tool invocation payloads to manage tool chaining. The server's `fastmcp` implementation uses strict Pydantic validation, which rejects this unexpected argument.

## Solution
Update all `@mcp.tool()` function signatures to include `wait_for_previous: bool | None = None` as an optional argument. This allows the server to accept the parameter without failing validation, effectively ignoring it.

## Status
Resolved via ADR-0008. Applied to `src/ripen/api/server.py` and `src/ripen/api/admin_server.py`.
