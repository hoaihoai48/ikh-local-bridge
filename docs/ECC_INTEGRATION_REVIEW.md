# ECC-Inspired Integration Review

**Date:** 2026-10-13  
**Target:** `hoaihoai48/ikh-local-bridge`  
**Reference:** [affaan-m/ECC](https://github.com/affaan-m/ECC)  
**Decision:** Adopt selected workflow principles; do not vendor the full ECC runtime.

## Why selective integration

ECC combines reusable Skills with plan/test/implement/review/verify workflows and security-oriented checks. Those principles fit a local, provider-independent Skill host. Many ECC components, however, are tied to Claude Code conventions (`.claude/`, hooks, slash commands, agent frontmatter) or require Node/npm and provider-specific agent capabilities. Copying them wholesale would couple Local Bridge to one harness and increase the trusted code surface.

## Adopt now: portable workflow contract

The Skill template now requires:
1. **Scope and plan:** state the task, inputs, outputs, and what is explicitly out of scope.
2. **Tests before implementation when changing code:** add a test that captures expected behavior, observe it fail when practical, implement the smallest change, then rerun the relevant test.
3. **Verification evidence:** list exact commands, exit codes, and observed outcomes. Mark anything not executed as `NOT RUN` / `UNVERIFIED`; never infer PASS from code inspection.
4. **Security review:** inspect manifest entrypoints and their imports/side effects; call out file writes, network use, subprocesses, credential access, and dependencies.
5. **Diff/output review:** summarize changed files and check that output artifacts meet the acceptance criteria.
6. **Final report:** separate verified facts, unverified claims, blockers, and remaining risks.

These are workflow requirements for Skills and AI-assisted work. They are not a claim that the current Bridge enforces every gate automatically.

## ECC component fit

| ECC idea/component | Decision | Reason |
|---|---|---|
| TDD workflow | Adopt the principle in the Skill authoring contract | Provider-independent and useful for deterministic tools |
| Verification loop | Adopt an evidence-based local checklist | Fits local testing; exact checks must be chosen for each repo |
| Security scan / AgentShield | Do not add as a Bridge runtime dependency | Its documented scan targets Claude Code configuration such as `.claude/settings.json`, hooks, and MCP config, not the Local Bridge Python Skill contract |
| Skill stocktake | Defer | A useful future local-library inventory, but not required for the current MVP |
| Hooks, agents, slash commands, memory, provider adapters | Do not import from ECC | Harness-specific or outside the current provider-independent runtime scope |
| ECC full install / npm package | Do not install automatically | No hidden provider dependency, global config mutation, or npm runtime requirement |

## Safety boundary

A valid manifest only makes a tool discoverable; it does not make the code safe. The current runner launches Python with the current OS user's permissions. The UI's `reviewed` acknowledgement is not an OS sandbox. Never auto-run newly imported Skills, auto-fix findings, install dependencies, access the network, publish, or push changes as part of verification without explicit user approval.

## Implementation scope in this branch

- Strengthen the portable Skill authoring template with explicit planning, TDD, verification evidence, and security review gates.
- Document which ECC ideas are adopted, deferred, or intentionally excluded.
- Do not add ECC dependencies or copy provider-specific hooks/configuration.
- Do not claim that tests passed: runtime tests must still be executed on the user's local machine unless actual execution evidence is available.

## Local verification checklist

From the repository root on macOS:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

Then manually inspect the template diff and create a disposable sample Skill before testing it through the UI. Record the actual command output; do not mark this document's checklist as passed merely because it exists.
