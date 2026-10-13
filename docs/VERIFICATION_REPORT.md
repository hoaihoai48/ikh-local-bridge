# Local Bridge Verification Status

## Architecture reset

The previous implementation was a multi-Skill catalogue plus a manifest-driven Python script runner. That did not meet the product requirement. The rebuild branch changes the intended runtime to one configured Skill, one workspace, and a local-first AI agent loop.

## Implemented in this branch

- One Skill file configured through IKH_BRIDGE_SKILL_FILE.
- One workspace configured through IKH_BRIDGE_WORKSPACE.
- SKILL.md is loaded into the agent's system instructions; no per-Skill manifest is needed.
- OpenAI-compatible chat completions with tool calling.
- Local endpoint defaulting to Ollama loopback; no automatic cloud fallback.
- Local tools for listing, reading, and writing workspace files and executing argv commands.
- Workspace path checks for file tools.
- Bounded agent/tool loop and tool transcript.
- Tests rewritten for local tool behavior and single-Skill task flow.

## Automated verification

GitHub Actions run 38391975720 completed successfully for Python 3.11 and 3.12. Both jobs passed dependency installation, compileall, and the unit/integration test suite. The tested code commit was 99c9484d50a96fa88511f14cb403db1ca1f08557; subsequent changes in this branch were documentation and the one-file smoke-test Skill example.

## Not yet verified

A real Ollama/model tool-calling run has not been executed. Automated tests mock the model response; they prove the local agent/tool loop structure, not compatibility with every installed model or successful end-to-end work with the curriculum Skill.

## Required gates before acceptance

1. Run python -m compileall -q src tests.
2. Run python -m unittest discover -s tests -v.
3. Start Ollama and pull a model that supports tool calling.
4. Configure a disposable Skill and workspace.
5. Run a task that writes and rereads a file; inspect both the artifact and tool transcript.
6. Stop Ollama and verify that the Bridge reports connection failure without cloud fallback.
7. Confirm traversal attempts are rejected.
8. Review subprocess security before using important files.

## Remaining limitations

- No full OS sandbox: command execution uses current-user permissions.
- Local image generation is not implemented by the text/coding model adapter.
- Long tasks are synchronous and have no cancel/streaming controls yet.
- The model can still make reasoning errors; verify important outputs independently.
