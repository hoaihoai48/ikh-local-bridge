---
name: local-bridge-discovery-test
description: Verify the Bridge discovers a Skill made of SKILL.md only.
---

# Local Bridge Discovery Test

## Goal
Confirm that the local Bridge discovers and displays a Skill folder with only this file.

## Acceptance criteria
- The Skill appears in the configured Skill Library.
- Its name and description are displayed.
- No manifest or script is required for discovery.

## Limitation
This is a discovery smoke test only. It does not execute an AI agent, call a model, create deliverables, or run curriculum validators.
