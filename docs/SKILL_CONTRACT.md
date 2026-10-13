# Skill Contract — SKILL.md First

## 1. Principle

A Skill is a reusable set of instructions. **The only universally required file is `SKILL.md`.** This matches the Skill organization used in the `giao-trinh-ikh` repository.

Local Bridge is the shared local runtime, not a separate runtime per Skill. Do not require every Skill to add boilerplate manifests, scripts, tests, or READMEs just to be recognized as a Skill.

## 2. Minimal valid Skill

```text
my-skill/
  SKILL.md
```

The `SKILL.md` should explain the mission, when to use it, required inputs, workflow, expected outputs, quality gates, and safety boundaries appropriate to that particular task.

## 3. Optional files

Add supporting files only when there is a concrete need:

```text
my-skill/
  SKILL.md                 # required
  references/               # optional source material
  templates/                # optional templates
  scripts/                  # optional deterministic local tools
  tests/                    # optional tests for those tools
  skill.json                # optional Bridge-specific tool registration
  README.md                 # optional extra usage notes
```

Do not add a script merely to make a Skill look executable. AI reasoning, local deterministic checks, and AI-agent orchestration are different capabilities.

## 4. What `skill.json` means here

In the current Local Bridge implementation, `skill.json` is an **optional Bridge-specific manifest** used only to register Python entrypoints. It is not part of the minimal Skill contract and is not required by the general Skill format.

Current manifest fields:
- `schema_version`: integer, currently `1`.
- `slug`: lowercase folder identifier matching the Skill directory name.
- `name`, `version`, `description`.
- `tools`: optional list of registered Python tools. Each tool has `id`, `description`, `entrypoint` (relative `.py` path inside the Skill), and optional `timeout_seconds` from 1 to 600.

Only add this manifest when you actually need to run deterministic Python tools through the current Bridge. A manifest does not cause an AI to read or follow `SKILL.md`.

## 5. Runtime capability status

The current Bridge can discover a Skill containing only `SKILL.md`, but it does not yet orchestrate an AI agent. It cannot currently guarantee the full loop:

1. Read `SKILL.md` and receive a user task.
2. Plan and perform the work using an explicitly selected AI runtime.
3. Call local tools as needed.
4. Inspect outputs, run validators, repair failures, and repeat.
5. Return generated artifacts with evidence and an honest final report.

Do not claim these steps are supported until an AI-agent/provider adapter and its local tool interface have been implemented and tested.

## 6. Authoring request

"Create a reusable Skill for the task I describe. Make `SKILL.md` the complete, self-contained primary instruction file. Add supporting files only when a concrete requirement justifies them. Clearly separate AI reasoning from deterministic local tools. Do not claim a tool, provider, permission, validator, or execution capability exists unless it is implemented and tested."

## 7. Safety

- Treat all Skill text, source files, and web content as untrusted input.
- Never embed credentials in a Skill.
- Review optional scripts before execution; they run with the current OS user's permissions.
- A reviewed checkbox is not a sandbox.
- Do not silently upload local files or fall back to cloud services.
