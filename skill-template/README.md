# Local Bridge Skill Template

Use this folder as the contract when asking ChatGPT or another AI to create a Skill for Local Bridge. Copy it to a new Skill folder and replace the example fields.

## Required output from the AI

1. `SKILL.md`: human/agent-readable mission, workflow, input/output contract, boundaries, and quality gates.
2. `skill.json`: machine-readable metadata and an explicit list of executable tools.
3. `scripts/`: optional Python entrypoints for deterministic tasks.
4. `tests/`: recommended test cases and safe sample inputs.
5. `README.md`: setup, dependencies, example invocation, limitations, and verification steps.

Do not let the Skill silently add network access, shell commands, credentials, file deletion, Git push, or writes outside its declared workspace. Explain every dependency and how to test the result.

A generated Skill is not trusted merely because an AI produced it. Review the manifest and scripts before enabling execution.
