# Local Bridge MVP

Local Bridge is a local-first host for reusable Skills created by the user with ChatGPT or another AI. It is **not** a separate bridge per Skill.

## MVP goals

- Discover Skill folders from a local Skill library.
- Read a small, provider-independent `skill.json` manifest.
- Expose a local UI and API for inspecting Skills and registered tools.
- Execute only explicitly registered Python entrypoints, without a shell.
- Persist job records in SQLite and record logs/results.
- Bind the server to loopback by default.

## Status

This is the first scaffold, not a security-certified or production-ready runtime. Existing Skills that do not yet have `skill.json` can be discovered by their `SKILL.md`, but cannot be executed until their tools are explicitly declared and reviewed.

## Requirements

- Python 3.11+
- Install dependencies in an isolated virtual environment.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ikh-bridge
```

Open http://127.0.0.1:8765.

Chi tiết cài đặt và cấu hình riêng cho macOS: xem [Hướng dẫn cài đặt macOS](docs/MACOS_SETUP.md) và [Báo cáo kiểm chứng](docs/VERIFICATION_REPORT.md).

## Skill library

Mặc định, Local Bridge sẽ tìm Skill theo thứ tự ưu tiên:
1. Biến môi trường `IKH_BRIDGE_SKILLS_DIR` (nếu có thiết lập).
2. Thư mục `skills/` trong thư mục hiện tại hoặc root của repo.
3. Thư mục Skill cá nhân tại `~/.ikh-skills`.

Điều này giúp **tách biệt hoàn toàn việc lưu trữ Skill khỏi repo giáo trình**. Bạn có thể đặt Skill ở bất kỳ đâu và trỏ `IKH_BRIDGE_SKILLS_DIR` tới đó.

A Skill may include:
- `SKILL.md`: instructions written for an AI/agent or human.
- `skill.json`: machine-readable runtime contract.
- `scripts/`: tool entrypoints explicitly declared in `skill.json`.

See `skill-template/` for the portable Skill contract. Keep each Skill's own requirements and assets within its folder where practical.

## Safety model (MVP)

- The server defaults to `127.0.0.1`; do not expose it to a LAN or public internet.
- The runner invokes Python entrypoints directly with an argument array; it does not use `shell=True`.
- Entrypoints must resolve inside their Skill directory.
- A manifest is a declaration, not proof that code is safe. Review new Skills and scripts before running them.
- Do not place API keys or credentials in Skills, manifests, logs, or the repository.
- This MVP does not call any AI provider automatically and has no implicit cloud fallback.
- No generic file-edit, Git-push, delete, or network tool is provided. However, a declared Python script runs with the current OS user's permissions and could still modify files or use the network. Review code first and use a disposable workspace for initial tests.
- Treat this as a development MVP; perform local tests and security review before using it on important files.

## Current limitations

- No AI provider adapter is wired yet.
- No fine-grained OS sandbox or per-path read/write enforcement yet. The UI requires an explicit acknowledgement before launching a declared script, but that is not a substitute for code review or OS isolation.
- No background queue or cancellation yet.
- Skills must expose explicit Python tools to be runnable.
- The current runner launches a declared script with no additional arguments, using the chosen workspace as its working directory and `IKH_BRIDGE_WORKSPACE` as an environment variable.
- Run output is captured in the job record; large-output management and robust process isolation are future work.

## Development checks

```bash
python -m compileall src
python -m unittest discover -s tests -v
```
