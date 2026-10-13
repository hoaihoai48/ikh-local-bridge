# iKH Local Bridge

Local Bridge is a **single local runtime shared by many Skills**. A Skill is primarily a folder containing one required file, `SKILL.md`. The Bridge may optionally expose deterministic local tools, but those tools are not required for a Skill to be a valid Skill.

## What this version does

- Discovers local Skill folders containing `SKILL.md`.
- Reads optional `skill.json` manifests when a Skill declares deterministic Python tools.
- Shows Skill metadata and registered tools in a local web UI.
- Runs only explicitly declared Python entrypoints, without `shell=True`.
- Stores tool-job history in SQLite.
- Binds to loopback by default.

## Important: what it does not do yet

**This version does not execute an AI agent or call an AI provider.** It cannot take an arbitrary task, make an AI follow `SKILL.md`, use tools iteratively, build multi-file deliverables, run validators, fix failures, and return a verified final package as one end-to-end workflow.

A Skill containing only `SKILL.md` is valid and discoverable, but this version can only display/discover it. The optional manifest is a Local Bridge tool-registration mechanism, **not a universal requirement for Skills**.

Do not treat the deterministic Python example as the intended end-to-end test. The real acceptance test must use `iKH Curriculum Authoring Skill v1.3` with an explicitly selected AI runtime/provider and local validators. That acceptance test is blocked until AI-agent orchestration is implemented.

## Requirements and setup

- Python 3.11+
- An isolated virtual environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ikh-bridge
```

Open http://127.0.0.1:8765.

See [macOS setup and test guide](docs/MACOS_SETUP.md), [Skill contract](docs/SKILL_CONTRACT.md), and [verification status](docs/VERIFICATION_REPORT.md).

## Skill library

The Bridge searches for Skills in this order:

1. `IKH_BRIDGE_SKILLS_DIR`, if set.
2. A `skills/` folder in the repository/current working directory.
3. `~/.ikh-skills`.

Example library:

```text
~/.ikh-skills/
  iKH-Curriculum-Authoring/
    SKILL.md
  another-skill/
    SKILL.md
    skill.json       # optional: only if registering Python tools
    scripts/         # optional: deterministic local helpers
```

Keep the Skill library independent of the curriculum repository if desired. Set `IKH_BRIDGE_SKILLS_DIR` to the parent folder containing Skill directories.

## Safety notes

- The web UI binds to `127.0.0.1` by default; do not expose it to a LAN/public internet.
- A manifest is a declaration, not proof that code is safe.
- Python tools run with the current OS user's permissions; there is no OS sandbox in this MVP.
- No cloud fallback or AI provider is called.
- Review scripts before running them. Do not put credentials in Skills, logs, or the repository.

## Development checks

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

These commands test the current deterministic Bridge scaffold only; they do not prove end-to-end AI Skill execution.
