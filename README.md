# iKH Local Bridge

**One running Local Bridge = one Skill + one local workspace.** It replaces the remote/server-side execution environment with local file and command execution. It is not a multi-Skill library manager.

The Bridge loads the selected Skill's `SKILL.md` as agent instructions, sends the task to the configured model, and exposes local tools so the agent can inspect and modify files and run checks in the workspace.

## Current architecture

- **One Skill:** configured by `IKH_BRIDGE_SKILL_FILE`, pointing directly to a single `SKILL.md`.
- **One workspace:** configured by `IKH_BRIDGE_WORKSPACE`.
- **Per-Skill UI:** place an optional `bridge-ui.html` next to that Skill's `SKILL.md` to replace the built-in home page with an interface designed specifically for that Skill. The custom UI can call `/api/status`, `/api/jobs`, and `POST /api/task`. See `docs/SKILL_CONTRACT.md`.
- **Built-in workbench:** if no custom UI exists, a dark responsive workbench identifies the active Skill, shows model/workspace status, accepts tasks, displays results, and lists recent jobs. This fallback is useful but is not a magically generated domain-specific interface.
- **Local-first model:** OpenAI-compatible local endpoint, defaulting to Ollama at `http://127.0.0.1:11434/v1`.
- **Agent loop:** model can call local tools repeatedly; Bridge returns tool results to the model until it finishes or reaches a bounded round limit.
- **Local tools:** list files, read/write text files, and run commands with argv (no shell invocation). File tools reject paths outside the workspace.
- **No implicit cloud fallback:** if the local model is unavailable, the task fails with an error. A remote HTTPS endpoint can be configured explicitly.
- **No per-Skill manifest:** `SKILL.md` is the required instruction file. No `skill.json` is needed to load it.

## macOS setup

Requirements: Python 3.11+, Git, and a local OpenAI-compatible model server. For the default setup, install Ollama from https://ollama.com/.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]"
    ollama pull qwen2.5-coder:7b

Configure one Skill and one workspace before starting the Bridge:

    export IKH_BRIDGE_SKILL_FILE="/absolute/path/to/your-skill/SKILL.md"
    export IKH_BRIDGE_WORKSPACE="/absolute/path/to/working-directory"
    export IKH_BRIDGE_MODEL="qwen2.5-coder:7b"
    export IKH_BRIDGE_MODEL_BASE_URL="http://127.0.0.1:11434/v1"
    ikh-bridge

Ensure Ollama is running, then open http://127.0.0.1:8765. The page identifies the one configured Skill, workspace, model and endpoint. See `docs/MACOS_SETUP.md`.

## Optional remote provider

A remote provider is not selected automatically. To use one, explicitly set its OpenAI-compatible HTTPS base URL, model name, and API key in the environment before starting the Bridge. The Skill text, task, and tool results will be sent to that provider. Never configure a remote provider if the task or workspace content must remain local.

## Tests

    python -m compileall -q src tests
    python -m unittest discover -s tests -v

These tests need to be run in the target local environment. Do not claim a test passed unless its output was actually observed.

## Security and limitations

- The Bridge binds to loopback by default. Do not expose it to a LAN or public internet.
- File tools enforce workspace path boundaries; this is not a full OS sandbox.
- Commands run with the current user's permissions. Review the Skill and use a dedicated workspace.
- The model must support OpenAI-compatible chat completions with tool calling.
- Local text/coding models do not automatically provide image generation. Image work requires a real image-capable local model/service and a corresponding adapter; this version does not pretend that capability exists.
- Agent orchestration is an initial implementation. Test with disposable workspaces before relying on it for important projects.
