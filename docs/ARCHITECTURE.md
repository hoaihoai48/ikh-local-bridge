# Local Bridge Architecture (MVP)

## Design principle

One Local Bridge runtime hosts many independently authored Skills. A Skill can be authored in ChatGPT or another AI, but its execution contract is provider-independent. Local Bridge does not generate or rewrite Skills automatically in this MVP.

## Components

- **Skill library:** local folders containing `SKILL.md`, optional `skill.json`, scripts, templates, and tests.
- **Manifest loader:** validates the small JSON contract and ensures declared Python entrypoints stay inside the Skill folder.
- **Registry:** discovers Skills and reports invalid manifests without stopping discovery of other Skills.
- **Tool runner:** executes only declared Python entrypoints, without a shell, with a timeout and captured output.
- **Job store:** records status, timestamps, exit code, stdout/stderr, and errors in SQLite.
- **Local UI/API:** provides Skill discovery, job history, and an explicit-confirmation action for declared tools.
- **Instance registry:** explicit allowlist of named, enabled workspace/Skill pairs; unknown and disabled IDs fail closed.\n- **MCP adapter:** optional stdio MCP server exposing a fixed set of workspace tools through the instance registry to a connected reasoning client; it does not generate content or call a model API. The registry is application-level authorization, not an OS sandbox.\n- **Provider adapters (future):** explicit provider selection and common interface; no implicit fallback to a cloud provider.

## Runtime lifecycle target

DISCOVER -> VALIDATE MANIFEST -> REVIEW PERMISSIONS -> PLAN -> WAIT FOR APPROVAL IF NEEDED -> RUN REGISTERED TOOLS -> VALIDATE OUTPUT -> RECORD EVIDENCE -> REPORT.

The runtime implements discovery, manifest validation, SQLite history, launching declared Python entrypoints after a UI/API acknowledgement, and a separate stdio MCP interface for a configured workspace. It does not implement OS-level isolation. Multi-workspace selection is available through an explicit application-level registry, but must not be described as a filesystem sandbox.

## Workspace and execution boundaries

- Bind to loopback only.
- Entry points must be declared in `skill.json` and resolve inside their Skill folder.
- The runner uses a direct argument list with `shell=False`.
- This first version passes only a small environment allowlist.
- A workspace is currently recorded and used as the process working directory; it is also exposed as `IKH_BRIDGE_WORKSPACE`. This is not an enforced filesystem sandbox. A Python tool runs with the current OS user's permissions and may modify files or access the network.
- Do not run unreviewed Skills against important data. A Python script can still perform arbitrary operations permitted to the user account.

## Future work

1. Add manifest schema tests and a safe example tool.
2. Add explicit per-tool argument schemas and user-confirmed execution plans.
3. Add subprocess isolation and enforce workspace read/write boundaries.
4. Add a per-instance registry and authorization model before allowing one connector to select among multiple workspaces.\n5. Add OS-enforced filesystem/process isolation.\n6. Add provider adapters with explicit credentials and no automatic cloud fallback.
5. Add approval gates, cancellation, artifact management, and package import/export.
6. Add an installer and platform-specific startup instructions.
