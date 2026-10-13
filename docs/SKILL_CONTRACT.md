# Skill Contract for Local Bridge

## Core rule

One running Local Bridge instance is configured for **one Skill**. The required Skill file is SKILL.md. The Bridge reads this file and places its contents into the agent's system instructions. No skill.json is required.

## Expected setup

    some-skill/
      SKILL.md                 # required
      scripts/                 # optional; if the task needs them
      references/              # optional; source materials
      templates/               # optional; reusable templates

The selected workspace is configured separately from the Skill directory. The Bridge executes file operations and commands in the workspace; the Skill directory provides instructions and any resources the Skill references.

## Execution lifecycle

1. The user starts a Bridge instance with one SKILL.md and one workspace.
2. The user submits a natural-language task in the local UI.
3. The Bridge sends the Skill instructions and task to the explicitly configured model endpoint.
4. The model can call local tools to list/read/write workspace files and run commands.
5. Tool results are sent back to the model for further work until it finishes or the round limit is reached.
6. The UI returns the model's final report and tool transcript. Actual test output must be inspected; model statements alone are not verification.

## Model endpoint policy

- Default: local OpenAI-compatible endpoint at http://127.0.0.1:11434/v1.
- No cloud fallback if the local model is unavailable.
- A remote endpoint must be explicitly configured with HTTPS. If selected, Skill instructions, task content, and tool results may be sent to that provider.
- The selected model must support tool calling.

## Available tools

- list_files(path): list entries inside the workspace.
- read_file(path): read a bounded-size UTF-8 text file inside the workspace.
- write_file(path, content): create or replace a UTF-8 text file inside the workspace.
- run_command(argv, timeout_seconds): execute a process in the workspace with shell=False.

File tools reject paths that resolve outside the workspace. Command execution is not a security sandbox: a command can have broader access under the current OS user's permissions. Use a dedicated workspace and do not run untrusted Skills without review.

## Capabilities not implied by SKILL.md

A Skill may instruct an AI to create images, use a browser, access the network, or call an external service. The instruction file alone does not provide these capabilities. They must exist as real, configured tools or model capabilities. The current runtime does not include a generic local image-generation adapter.

## Quality and final report

The agent must distinguish actions actually performed via tools, checks actually run and their observed output, outputs created, unresolved failures, and checks not run or not verified. Never claim PASS solely because the model says a task is complete.
