# Session Reporting

Use session reports as the durable handoff trail for Ape Adventure. The source pattern is:

`C:\Users\sarut\Documents\Games Development Hub\cryptic-grove\Session Reports\Session Report Template.md`

This adaptation keeps the same intent but adds game-development fields for feel, stability, assets, and validation.

## Standard Flow

1. At the start of a meaningful session, note the objective, branch, instruction files read, and current repo state.
2. During the session, track mechanics touched, files changed, decisions made, validation run, and risks found.
3. Before handoff, run the expected compile and smoke checks for the area touched.
4. Create or update a report in `Session Reports/`.
5. Keep the report concise enough that the next agent can resume in under a minute.

## Filename

Use:

`yyyy-mm-dd-session-report-ape-adventure.md`

If multiple reports are needed on the same day, add a short suffix:

`yyyy-mm-dd-session-report-ape-adventure-player-physics.md`

Use lowercase, hyphens, no spaces, and stable slugs.

## Game-Dev Session Report Template

```markdown
---
type: "[[Session Reports]]"
status: draft
created: "[[YYYY-MM-DD]]"
updated: "[[YYYY-MM-DD]]"
date: "[[YYYY-MM-DD]]"
project: "[[Ape Adventure]]"
repo: ape-adventure
repo_slug: ape-adventure
branch:
workspace: "C:\\Users\\sarut\\Documents\\Games Development Hub\\Ape Adventure"
session_kind: build | debugging | playtest | art | audio | design | maintenance | release | mixed
session_scope:
objective:
operator:
llm:
  - "[[ChatGPT]]"
model:
agents_used:
  - "[[Codex]]"
agent_instruction_files:
  - "[[AGENTS.md]]"
  - "[[CLAUDE.md]]"
  - "[[docs/SESSION_REPORTING.md]]"
related_systems:
  - "[[Github]]"
  - "[[pygame]]"
tags:
  - session-report
  - ai-workflow
  - game-dev
  - ape-adventure
commit_count:
files_changed:
tasks_completed:
tasks_remaining:
confidence: medium
---

# YYYY-MM-DD Session Report - Ape Adventure

## Session Snapshot

- Date:
- Branch:
- Session kind:
- Primary objective:
- Outcome status: draft | active | complete | blocked
- Current playable target:
- Instruction files read:

## Executive Summary

- Mission:
- Material changes:
- Decisions that matter next:
- What the next agent should know in under 60 seconds:

## Work Completed

### Gameplay / systems touched

- Movement:
- Camera:
- Collision:
- Enemies:
- Collectibles:
- Level flow:
- UI / HUD:
- Audio:
- Assets:

### Files created

- `path/to/file`

### Files modified

- `path/to/file`

## Feel and Stability Notes

- Movement feel:
- Jump / roll / enemy-contact feel:
- Camera readability:
- Collision reliability:
- Death / respawn / results flow:
- 90s platformer presentation notes:
- Any mechanic removed, renamed, or intentionally deferred:

## Asset Notes

- Assets added:
- Source / license:
- Placeholder or final:
- PixelLab / generated asset IDs:
- Art direction fit:
- Follow-up needed:

## Decisions and Reasoning

- Decision:
  Why it was chosen:
  Tradeoff accepted:

## Validation

- Compile checks:
- Smoke tests:
- Manual playtest:
- Screenshots / GIFs:
- Performance risks:
- What remains unverified:

## Git and Delivery Log

- Commits:
- Branch / PR:
- Push status:
- Release / build status:

## Tasks

### Completed

- [x] Task #task

### Open / remaining

- [ ] Task #task #inbox

### Immediate next actions

- [ ] Task #task #next

## Blockers and Risks

- Current blocker:
- Dependency on human input:
- External dependency:
- Risk to watch next session:

## Handoff for Future Agents

- Current repo state:
- Highest-value next step:
- Files to read first:
- Known traps or anti-patterns:
- Safe assumptions:
```

## Notes

- Link generously when using an Obsidian vault, but keep repo paths plain and exact.
- For code sessions, validation should include `py -m compileall -q ape_adventure` and any relevant smoke tests.
- If `ape_escape.py` is touched, also run `py -m py_compile ape_escape.py` and the legacy smoke test.
- For visual sessions, record what was checked in motion, not only what looked good in a still frame.
- For asset sessions, record source, license, dimensions, intended animation frames, and whether the asset is placeholder or shippable.
