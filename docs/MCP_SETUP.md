# Standalone MCP Setup and Workspace Profiles

This guide configures the standalone Bridge as a local stdio MCP server. The model/reasoning remains in ChatGPT or another connected client; this process does not call an AI provider API.

## Install

```bash
git clone https://github.com/hoaihoai48/ikh-local-bridge.git
cd ikh-local-bridge
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Configure instances for one connector

Copy [examples/instances.example.json](../examples/instances.example.json) to a private local path (not into a public repository), replace every placeholder with an existing absolute path, and set `enabled: true` only for instances you have reviewed. Keep one distinct workspace per course/project. The registry fails closed for unknown/disabled IDs and requires the configured workspace and Skill file to exist.

Set the config before starting the MCP server:

```bash
export IKH_BRIDGE_INSTANCES_CONFIG="$HOME/.config/ikh-local-bridge/instances.json"
.venv/bin/ikh-bridge-mcp
```

Call `list_bridge_instances` first, then pass the selected `instance_id` to `get_bridge_status`, `get_curriculum_skill`, and each workspace tool. The registry is application-level authorization only; scripts run with the current OS user's permissions.

### Legacy single-instance profile

For a one-workspace setup without a registry, use the environment variables below.

## Configure one isolated profile

A profile is a separate process configuration, not a security sandbox. Give each profile an explicit workspace, canonical Skill path, Skill library, and SQLite job database. Do not point a profile at your whole home directory.

Example for an isolated Python Level 2 pilot (replace the absolute paths with paths that exist on your Mac):

```bash
export IKH_BRIDGE_WORKSPACE="$HOME/ikh-workspaces/python-bang-a-level-2-pilot"
export IKH_BRIDGE_SKILL_FILE="$HOME/.ikh-skills/ikh-curriculum-authoring/SKILL.md"
export IKH_BRIDGE_SKILLS_DIR="$HOME/.ikh-skills"
export IKH_BRIDGE_DB="$HOME/.ikh-local-bridge/python-level-2-pilot.sqlite3"
.venv/bin/ikh-bridge-mcp
```

The workspace directory and Skill file must exist. Keep the canonical curriculum source read-only by convention and direct all generated output to a dedicated disposable workspace. Application-level path checks are not an OS sandbox: reviewed Python scripts can still use the current user's permissions.

## ChatGPT Secure MCP Tunnel

Use the official OpenAI Secure MCP Tunnel documentation and the existing `tunnel-client` installed from an official source.

### Reuse the existing tunnel

If the existing `ikh-curriculum` tunnel is the intended tunnel for this Bridge, reuse its existing `tunnel_id`; do not create another tunnel or runtime key merely because the local MCP command changes. OpenAI's Secure MCP Tunnel documentation explicitly supports using the same `tunnel_id` with `tunnel-client`. Tunnel organization/workspace association and permissions still need to be correct.

Before switching the active server:

1. Inspect the current profile and record its non-secret settings (profile name, tunnel ID, MCP command, workspace/Skill paths, and current health/readiness). Never print or copy secret values.
2. Validate the new `.venv/bin/ikh-bridge-mcp` command locally, including MCP `initialize`, `tools/list`, and representative `tools/call` operations, using a disposable workspace.
3. Back up the existing profile securely, excluding secrets from reports and source control.
4. Plan a short cutover window. With stdio MCP bindings, OpenAI's `tunnel-client` supports only one active `tunnel-client` process per tunnel ID. Do not run old and new stdio clients concurrently on the same tunnel ID.
5. Stop the existing tunnel-client process, change only its MCP command/profile target to the new Bridge, and start it again using the same tunnel ID and existing runtime key.
6. Run `tunnel-client doctor --profile <existing-profile> --explain`, verify readiness/active polling, then test the existing ChatGPT connector. If tool discovery or calls fail, stop the new process and restore the saved profile/command before restarting the old server.
7. Do not declare cutover successful until a real ChatGPT conversation calls `get_bridge_status`, `list_files`, a disposable `write_file`/ `read_file` pair, and a reviewed harmless validator successfully.

This is a controlled replacement, not a parallel pilot. The active connector may be temporarily unavailable during the switch. If zero downtime is mandatory, a separate tunnel ID and connector would be required; that is not the preferred path for this user's current goal.

### Secret and permission requirements

- Keep `CONTROL_PLANE_API_KEY` outside Git and never send it to ChatGPT or include it in reports.
- Do not create a new runtime key unless the existing one is invalid or lacks required `Tunnels Read + Use` permissions.
- Use the ChatGPT workspace's supported custom MCP connector flow and permissions. Platform tunnel permissions and ChatGPT workspace permissions are separate.
- A successful `tunnel-client doctor` is only a transport preflight, not proof that a real ChatGPT tool call succeeds.

## Required smoke test

1. Start the pilot MCP server/tunnel with the dedicated profile.
2. From a new ordinary ChatGPT conversation, select the pilot connector.
3. Call `get_bridge_status`, then `get_curriculum_skill`; confirm returned paths match the pilot workspace and canonical Skill.
4. Call `list_files` on the pilot workspace.
5. Create a unique test Markdown file only inside the pilot workspace using `write_file`; read it back with `read_file`.
6. Run a harmless, pre-reviewed validator with `run_command`; capture actual output and exit code.
7. Do not delete anything unless a dedicated cleanup tool is present and the exact target was created by this test. Otherwise leave it and report its path.
8. Verify that the active existing connector still works independently.

Record the exact OS, Python version, commands, tunnel profile name (not its secrets), tool outputs, and failures. Mark the end-to-end gate NOT VERIFIED until these calls have actually succeeded from the intended ChatGPT conversation.

## Current limitation

The standalone Bridge supports an explicit instance registry and rejects unknown/disabled instance IDs. This is an application-level boundary, not an OS sandbox: malicious Python scripts may still access files permitted to the current user. Keep each workspace least-privilege and never treat the registry as OS-enforced isolation.
