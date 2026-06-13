# ADR-0006: Removal of Authentication Logic and Transport Naming Unification for MVP

- **Date**: 2026-06-13
- **Status**: Proposed
- **Deciders**: Gemini CLI (Agent), ayato-labs (User)

## Context
The Ripen MVP currently contains a legacy authentication logic (inherited from the "Shared Memory" project phase) that relies on environment variables like `RIPEN_API_KEY` and local files like `auth.json`. This logic is causing "Authentication required" errors for users who have not explicitly configured these keys, creating friction in the core value proposition of the product (knowledge persistence and retrieval).

Additionally, the codebase uses inconsistent terminology for the transport layer, frequently referring to "SSE" (Server-Sent Events) while the underlying implementation has moved to "Streamable HTTP" as per FastMCP v3.0 standards.

## Decision
1.  **Remove Authentication Logic for MVP**: We will disable the `AuthMiddleware` and remove dependencies on `RIPEN_API_KEY`, `SHARED_MEMORY_API_KEY`, and `auth.json`. All requests will default to a single user (`default_env_user` or the OS username) without requiring a token.
2.  **Unify Transport Terminology**: Rename internal variables, configuration keys, and log messages from "SSE" to "Streamable HTTP" (or simply "HTTP") to align with current architectural standards.
3.  **Defer Advanced Auth**: Robust authentication (JWT, multi-user isolation) will be reconsidered as a post-MVP feature once the core memory functions are stabilized and verified in team environments.
4.  **Adopt Dynamic Health Checks for System Tests**: Replace fixed `time.sleep()` calls in system test fixtures with dynamic health check loops. This ensures tests wait the minimum necessary time for the server to be ready while providing a longer overall timeout for slower CI/CD environments.

## Consequences
### Positive
- **Reduced Friction**: Users can start the Hub and connect agents without troubleshooting authentication errors.
- **Architectural Clarity**: Removal of legacy/unused code paths simplifies debugging and future development.
- **Improved Documentation**: Aligning code terminology with FastMCP standards makes the system easier to understand for new contributors.
- **Reliable CI/CD**: Dynamic health checks eliminate race conditions in system tests, reducing flaky build failures.

### Negative / Risks
- **No Access Control**: In the MVP phase, any agent on the same network (if host is `0.0.0.0`) can read/write to the hub. This is accepted for the current development stage and LAN-only use cases.

## References
- Issue: #180
- Related: [FastMCP Streamable HTTP Documentation]
