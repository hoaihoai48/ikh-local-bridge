# Standalone Bridge Architecture & Migration Plan

Date: 2026-10-14
Status: implementation plan / migration gate (not a claim of completed runtime verification)

## Decision

`hoaihoai48/ikh-local-bridge` is the canonical home for the reusable local runtime, MCP-facing adapter, instance registry/manager, tunnel lifecycle integration, operational documentation, and their tests.

`DKTECHVN/giao-trinh-ikh` remains the source of truth for curriculum content, authoring instructions, course-specific validators, lesson maps, provenance ledgers, and course QA reports. It may document how to connect to a Bridge, but must not become the canonical runtime implementation.

Do not delete or disable existing tunnel/MCP code until parity is demonstrated and the owner explicitly approves cutover.

## Current baseline observed from repository

- Python package `ikh-local-bridge`, version 0.1.0; FastAPI/uvicorn; loopback-first.
- Skill discovery supports `IKH_BRIDGE_SKILLS_DIR`, a local `skills/` folder, and `~/.ikh-skills`.
- Skills with a `skill.json` manifest can expose declared Python entrypoints.
- API/UI, SQLite job history, manifest/path checks, and unit/integration tests exist.
- Runner uses a direct subprocess argument list with `shell=False`, but a declared Python script still inherits the OS user's effective filesystem/network authority.
- The README explicitly says no AI provider adapter is wired, and fine-grained per-path enforcement/OS sandboxing are not implemented.
- The existing curriculum repository contains separate MCP/tunnel work. Its behavior must be audited against this runtime before any code is moved or retired.

## Vocabulary (keep these concepts separate)

- **Bridge runtime:** the local service that discovers Skills and executes reviewed tools.
- **Bridge instance:** one configured runtime context with its own identity, workspace, Skill library, data/log store, and permission policy.
- **MCP connector/adapter:** exposes a deliberately small set of Bridge capabilities to ChatGPT through the configured MCP transport.
- **Tunnel:** transport/lifecycle mechanism used when ChatGPT cannot reach the local endpoint directly.
- **Skill:** portable instructions and declared tools; not a runtime instance and not an AI provider.

A single reusable connector may address multiple explicitly configured instances. It must not gain implicit access to every directory on the host.

## Required target architecture

1. **Instance registry**
   - Stable instance ID and human-readable name.
   - Explicit workspace and Skill-library roots.
   - Separate per-instance configuration and job database/log namespace.
   - Disabled-by-default instances until reviewed.
   - Resolve all paths and reject roots that escape the configured instance roots.
   - Never infer an instance from arbitrary user-provided filesystem paths.

2. **Permission boundary**
   - Separate read-only operations from write/execute operations.
   - Per-instance and per-tool allowlists.
   - Confirm writes/execute actions with a clear preview of affected paths and action.
   - Default-deny network access where practical; disclose that process-level checks are not an OS sandbox.
   - Never store credentials in Skill manifests, logs, or committed config.
   - Do not advertise filesystem isolation until it is enforced by an OS-level boundary or equivalent tested mechanism.

3. **MCP adapter**
   - Expose only named, schema-validated operations, not arbitrary shell access.
   - Resolve all operations through the instance registry and existing Bridge service layer.
   - Keep transport/authentication concerns outside curriculum Skill code.
   - Reject unknown instance IDs and operations; cap input/output sizes and execution time.
   - Keep compatibility with the currently configured ChatGPT connector until an acceptance test passes.

4. **Transport/tunnel integration**
   - Isolate tunnel lifecycle from Skill execution.
   - No automatic public bind; runtime remains loopback-only.
   - Secrets/tokens live in local ignored configuration or OS keychain, never in Git.
   - Startup, health check, shutdown, stale tunnel detection, and recovery must be observable.
   - Do not replace the active tunnel or connector during development.

5. **Portable Skill contract**
   - Continue supporting `SKILL.md` as human/agent instructions.
   - Use `skill.json` only for explicit runtime capabilities and validated tool metadata.
   - Keep course-specific validators and authoring workflow in the curriculum repository.
   - The Bridge may run a declared validator against a designated workspace, but must not claim academic correctness merely because a script exits zero.

## Safe implementation sequence

### Phase 1 — inventory and compatibility map
- Inventory runtime, MCP server/connector, tunnel scripts, configuration, launch instructions, and tests in both repositories.
- Map each existing capability to one canonical owner.
- Identify duplicated code and incompatible protocols before moving files.
- Record current working connector/tunnel behavior and rollback steps.
- No deletion, merge, active configuration change, or secret migration.

### Phase 2 — runtime hardening
- Add tests for path traversal, symlinks, invalid instance roots, cross-instance access, oversized output, timeouts, and denied operations.
- Add a versioned instance configuration schema and deterministic resolution.
- Ensure a requested workspace is selected from a registered instance, not accepted as an unrestricted arbitrary path.
- Document which guarantees are code-enforced and which remain advisory.

### Phase 3 — MCP adapter and transport
- Move/adapt the connector implementation into this repository only after the inventory confirms the protocol and dependencies.
- Add MCP tool schemas and contract tests.
- Keep current ChatGPT connector configuration intact while a new endpoint is tested side by side.
- Add lifecycle/health/rollback docs; never commit live credentials.

### Phase 4 — isolated pilot
- Create a dedicated Python Level 2 test instance with a disposable workspace and read-only curriculum source by default.
- First run discovery and read-only validation. Enable writes only for an explicitly designated output directory.
- Use a tiny harmless test Skill to prove discovery, tool call, output capture, and job logging before any curriculum operation.
- Validate actual generated/changed files with the course's canonical validator separately.
- Mark importer, web preview, academic correctness, and ChatGPT end-to-end as NOT VERIFIED unless directly tested.

### Phase 5 — acceptance and cutover decision
Required evidence before cutover:
- Unit/integration/security tests pass in a real local checkout.
- Existing ChatGPT connector/tool call is reproduced on the new path.
- Read-only and write operations are demonstrated against separate test directories.
- A failed or interrupted tunnel can be detected and recovered without exposing the service publicly.
- No secrets or unrelated workspace files are reachable through the connector.
- Existing configuration can be restored using documented rollback steps.

Only after all gates pass should the owner choose whether to switch the active connector/tunnel. Do not auto-merge this work or change production settings.

## Acceptance matrix

| Gate | Required evidence | Current status |
|---|---|---|
| Standalone runtime baseline | Existing unit/integration tests run locally from a clean checkout | Reported in existing verification doc; not rerun in this session |
| Instance isolation | Cross-instance path and tool access tests | NOT IMPLEMENTED / NOT VERIFIED |
| Per-path read/write enforcement | Adversarial filesystem tests against an enforced boundary | NOT IMPLEMENTED / NOT VERIFIED |
| MCP protocol compatibility | MCP initialize/list-tools/call contract tests | NOT VERIFIED for this standalone repository |
| ChatGPT end-to-end | A real tool call from normal ChatGPT Chat using the new connector | NOT VERIFIED |
| Tunnel lifecycle | Startup/health/shutdown/recovery tests on macOS | NOT VERIFIED in this session |
| Python Level 2 pilot | Isolated workspace run with captured evidence and validator output | NOT RUN |
| Existing setup preserved | Side-by-side test and rollback proof | NOT RUN |

## Reporting rule

Never report overall PASS based only on unit tests, a successful health endpoint, static validation, or an Antigravity summary. Report each gate as PASS, FAIL, NOT VERIFIED, or BLOCKED with direct evidence and the exact commit/test command.
