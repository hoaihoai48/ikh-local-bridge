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

Use the official OpenAI Secure MCP Tunnel documentation and the existing tunnel-client installed from an official source. Configure a tunnel profile whose MCP command points to the absolute path of this repository's `.venv/bin/ikh-bridge-mcp`. Do not reuse or overwrite the existing `ikh-curriculum` tunnel profile during initial testing; create a distinct pilot profile and tunnel ID.

- Keep the active, existing connector/tunnel untouched while testing.
- Keep `CONTROL_PLANE_API_KEY` outside Git and never send it to ChatGPT.
- Use the ChatGPT workspace's supported custom MCP connector flow and permissions.
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
