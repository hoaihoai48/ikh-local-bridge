# Portable Skill Contract v1

## Purpose

A Skill is authored by the user with ChatGPT or another selected AI. Local Bridge is the shared runtime; do not create one Bridge per Skill.

## Expected Skill folder

```text
my-skill/
  SKILL.md           # required human/agent workflow
  skill.json         # required before Local Bridge can run tools
  README.md          # setup, usage, limitations
  scripts/           # optional deterministic local tools
  tests/             # recommended tests and fixtures
  references/        # optional source material/templates
```

## Manifest v1

`skill.json` is JSON with:
- `schema_version`: integer, currently `1`.
- `slug`: unique lowercase folder identifier; must equal the folder name.
- `name`, `version`, `description`.
- `tools`: list of explicitly registered Python entrypoints. Each tool has `id`, `description`, `entrypoint` (relative .py path inside the Skill), and optional `timeout_seconds` from 1 to 600.

This initial runtime does not yet support arbitrary tool arguments, provider declarations, network permissions, file-write permissions, or approval policies in the manifest. Do not invent those fields and assume the runtime enforces them.

## Authoring request you can give an AI

"Create a reusable Skill for the task I describe, following the attached Local Bridge Skill Contract v1 and template. First inspect the provided sample and any sources I explicitly allow. Create SKILL.md, skill.json, README.md, deterministic scripts only where they reduce repeated work, and tests with safe fixtures. Do not add undeclared permissions, credentials, arbitrary shell execution, or network access. Ensure each manifest entrypoint exists within the Skill folder. Explain which steps require AI and which can run deterministically. Run available tests, report exact commands and outcomes, and label anything not actually tested as unverified. Do not claim compatibility with Local Bridge features that this contract does not implement."

## Trust and compatibility

- A manifest makes a tool discoverable, not trusted.
- Review scripts before execution; Python can access whatever the current OS user can access.
- Skills without a valid manifest may be listed for discovery but are not runnable.
- Contract compatibility does not imply task correctness. Each Skill needs task-specific tests and acceptance criteria.
