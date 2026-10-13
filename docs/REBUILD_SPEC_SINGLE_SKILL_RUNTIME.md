# Rebuild Spec: Single-Skill Local Execution Runtime

## Correct product definition

One Local Bridge instance represents **one selected Skill and its working environment**. It is not a Skill library manager and does not enumerate many Skills. The user supplies a folder containing the Skill's `SKILL.md` and chooses a local workspace. The Bridge loads that Skill's instructions into an agent runtime and performs the task on the user's machine.

## Responsibility split

- **AI model:** interprets the request, follows the supplied `SKILL.md`, plans work, requests tools, reviews results, and iterates.
- **Local Bridge:** hosts the agent loop, reads the selected Skill, exposes approved local tools, executes file operations/commands on the local machine, captures logs, and returns artifacts/evidence.
- **Model runtime:** local-first. The default endpoint is a local OpenAI-compatible endpoint (for example, Ollama). A remote endpoint is allowed only when the user explicitly configures it; no implicit cloud fallback.
- **Workspace:** one explicitly selected directory where the agent is expected to work. File tools must reject paths that resolve outside it.
- **Skill:** `SKILL.md` is the required instruction file. No `skill.json` is required. Additional scripts/resources are used only when the Skill itself needs them.

## User flow

1. Start the Bridge locally.
2. Configure the one Skill directory and one working directory.
3. Configure a model name and local OpenAI-compatible endpoint; default endpoint is loopback.
4. Enter a task and explicitly start the run.
5. The agent receives the full `SKILL.md`, task, workspace details, and tool definitions.
6. The agent calls local tools iteratively: list/read/write files, inspect outputs, and run commands in the workspace.
7. The Bridge shows the transcript/tool log, generated artifacts, and actual errors. It never marks a task as verified just because the model says it passed.

## Non-goals

- No multi-Skill catalog/selector.
- No required per-Skill manifest.
- No requirement to route tasks through ChatGPT's web UI or server filesystem.
- No implicit upload of workspace contents to a remote provider.
- No claim that local model inference is available until the user installs/configures a compatible local model server.
- No assumption that every model can generate images. Image generation requires an actual local image model/tool endpoint supported by the selected runtime.

## Implementation gates

- [x] Single Skill path and workspace configuration.
- [x] Load `SKILL.md` as agent instructions.
- [x] Local-first OpenAI-compatible model client, no fallback.
- [x] Tool-calling loop with bounded iterations and timeouts.
- [x] Workspace-confined list/read/write tools.
- [x] Explicit local command execution and visible logs.
- [x] Task/run history and truthful status.
- [x] Initial tests for traversal protection, tool calls, local command execution, and task flow. Missing-model/iteration-cap coverage remains to be expanded.
- [ ] Real-model smoke test on macOS and end-to-end verification with the intended Skill.

## Security boundary

Path validation prevents file tools from escaping the workspace, but subprocesses are not a complete OS sandbox. Commands run with the user's permissions and may access other resources. The UI must state this clearly and require explicit user initiation for each task. Do not bind to LAN/public interfaces by default.
