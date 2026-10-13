---
name: my-skill
description: State the task this Skill performs and the situations in which it should be used.
---

# Skill Name

## Mission
Describe the task and what a successful result looks like.

## When to use
State the activation criteria and when this Skill should not be used.

## Inputs
List required inputs, optional inputs, expected formats, and assumptions that must be confirmed.

## Workflow
Write the actual task-specific process in clear, ordered steps. Do not leave generic placeholders in a finished Skill. Distinguish AI reasoning from steps that can be checked deterministically.

## Outputs
Name the expected files or deliverables and where they should be created.

## Quality gates
Define objective acceptance criteria and the evidence needed to pass each one. Do not report PASS without running the check and inspecting its result.

## Safety boundaries
State which files and external sources may be accessed, which actions require approval, and whether network access or external providers are allowed. Never embed secrets.

## Final report
Require a concise summary of outputs, checks actually run, evidence, unresolved issues, and any items not verified.

---

This template is a single-file starting point. Add scripts, references, tests, manifests, or other support files only when the Skill has a concrete need for them.
