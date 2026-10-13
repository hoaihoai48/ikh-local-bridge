---
name: local-bridge-smoke-test
description: Verify that one SKILL.md can guide a local agent to create and reread a workspace file.
---

# Local Bridge Smoke Test

## Mission
Verify the single-Skill Local Bridge can load this Skill, use local file tools, and return evidence.

## Workflow
1. List the workspace root.
2. Create hello.txt in the workspace root with exactly this content: LOCAL_BRIDGE_SMOKE_TEST=PASS
3. Read hello.txt back using the local read_file tool.
4. Compare the observed file content with the required exact text.
5. Report PASS only if the file was created and the read-back content matches exactly. Otherwise report FAIL and include the actual tool error.

## Output
Create only hello.txt. Do not modify other files for this smoke test.

## Safety
Do not read or write outside the selected workspace. Do not run unrelated commands.

## Final report
State which file was created, the exact content observed on read-back, and whether the acceptance condition passed.
