# ADR-0008: MCP Tool Compatibility Layer

- **Date**: 2026-06-14
- **Status**: Accepted
- **Deciders**: AI Agent

## Context
Gemini CLI and similar MCP clients inject a `wait_for_previous: bool` parameter into tool invocations to manage parallel or sequential tool execution. The current `fastmcp` implementation on the Ripen server uses strict Pydantic validation for tool arguments, which rejects this unexpected `wait_for_previous` argument, causing a `ValidationError`.

## Decision
All `@mcp.tool()` function signatures in the Ripen codebase will be updated to include `wait_for_previous: bool | None = None` as an optional argument. This acts as a compatibility layer to allow the server to accept and gracefully ignore the parameter injected by the client, ensuring interoperability.

## Consequences
### Positive
- Eliminates `ValidationError` crashes when invoked from clients like Gemini CLI.
- Maintains strict validation for all other required arguments.
### Negative / Risks
- Adds a small amount of boilerplate code to every tool definition.
- Requires maintenance if the MCP protocol or the client injection behavior changes.

## References
- Issue: N/A (Internal Error)
- PR: N/A
