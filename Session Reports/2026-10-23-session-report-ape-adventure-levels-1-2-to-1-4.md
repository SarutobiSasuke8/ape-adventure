---
type: "[[Session Reports]]"
status: complete
created: "[[2026-10-23]]"
updated: "[[2026-10-23]]"
date: "[[2026-10-23]]"
project: "[[Ape Adventure]]"
repo: ape-adventure
repo_slug: ape-adventure
branch: claude/ape-levels-1-2-to-1-4-20261023
session_kind: build
session_scope: Tangle Jungle levels 1-2, 1-3 and 1-4, level progression, completability proof
objective: "Build playable levels 1-2 to 1-4 on 1-1's structure and difficulty curve, each adding one mechanic, and prove each can be finished."
operator: Alexei Udall
llm:
  - "[[Claude Code]]"
model: claude-opus-5-5
agents_used:
  - "[[Claude Code]]"
agent_instruction_files:
  - "[[CLAUDE.md]]"
  - "[[AGENTS.md]]"
  - "[[docs/SESSION_REPORTING.md]]"
  - "[[docs/GAME_DESIGN.md]]"
  - "[[docs/ROADMAP.md]]"
related_systems:
  - "[[Github]]"
  - "[[pygame]]"
  - "[[pytmx]]"
tags:
  - session-report
  - game-dev
  - ape-adventure
  - level-design
commit_count: 1
files_changed: 20
tasks_completed: 6
tasks_remaining: 6
confidence: high
---

# 2026-10-23 Session Report - Ape Adventure: levels 1-2 to 1-4

## Session Snapshot

- Branch: `claude/ape-levels-1-2-to-1-4-20261023`, cut from `origin/master` (the repo has no `main`; `master` is the default branch).
- Outcome: complete. All four Tangle Jungle levels load from `.tmx`, chain 1-1 -> 1-2 -> 1-3 -> 1-4 -> title, and each is finished by a scripted run with 0 hits and 0 deaths.
- Current playable target: the full World 1 vertical slice route, title to world clear.

## Level map summary

Grid is 32 px tiles, 18 rows; ground surface is row 16 in every level. A full running jump clears about 5.3 tiles and rises 95 px (measured with the real physics).

### 1-1 First Steps (unchanged, the baseline)

- Mechanic: walk, run, jump, stomp.
- Layout: 110 cols. Two 3-tile pits, seven low platforms, 4 Snappers and 1 Hopper, 28 bananas, 4 letters.
- Difficulty: generous; pits are 2 tiles inside jump range.

### 1-2 Vine Valley

- Mechanic introduced: vine swing. Jump into a vine, hold left/right to pump, jump to let go on the forward swing.
- Layout: 130 cols. Gap A (cols 16-23) is the teaching vine: one vine 2 tiles off the ledge, bananas tracing the arc. Gap B (40-47) puts letter A2 at the top of the swing. A 3-tile pit (56-58) gives a breather. Gap C (64-77) is 14 tiles wide and needs two vines back to back, with letter P between them. Gap D (96-103) lands into a Hopper. 5 vines, 4 Snappers, 3 Hoppers, 42 bananas, 4 letters.
- Difficulty notes: every vine gap is 8+ tiles, so it cannot be jumped (tested). Enemies are kept at least 5 tiles from each take-off so a stomp bounce does not throw the player into a gap. The twin-vine gap is the skill check.

### 1-3 Hollow Log Run

- Mechanic introduced: rolling under hollow logs. A log is a solid trunk (rows 12-14) over a one-tile tunnel. Bongo stands 44 px, so he must roll (24 px hitbox); when the roll ends under the log he crawls, and can chain rolls. The log top is 128 px up, too high to jump.
- Combines: the roll attack from 1-1, now required against Snappers inside the tunnels.
- Layout: 140 cols. Log 1 (cols 14-19) is empty with bananas inside. An open-ground Snapper (col 25) for roll practice. Pits grow to 4 tiles (30-33, 60-63, 110-113). Log 2 (38-47) hides a Snapper and letter A2. A step block (66-67) offers a high route along the top of log 3 (letter P) or the tunnel below. Log 4 (94-105) hides two Snappers. 7 Snappers, 3 Hoppers, 41 bananas, 4 letters.
- Difficulty notes: tighter pit timing (take-off window about 2 tiles), enemies in confined space, a choice of route.

### 1-4 The Saurian's Arena

- Mechanic: boss pattern read and punish. Combines stomp (1-1) with timing.
- Layout: 30 cols, one screen. Arena walls at both ends; a 3-tile, 2-high safe ledge at each end. King Saurus (56 px tall, so the 64 px ledge clears his head) telegraphs, charges the player, crashes into a ledge face and is dazed. Stomp him while dazed. Rolling into him, or stomping him when he is not dazed, does nothing to him. 3 hits. Each hit raises the phase: charge 210 -> 270 -> 330 px/s, telegraph 0.9 -> 0.7 -> 0.5 s, daze 1.8 -> 1.4 -> 1.05 s, and from phase 2 he hops part-way through the charge. The goal totem appears only after he is beaten. 6 bananas, no letters.
- Difficulty notes: safe if the player waits on a ledge and reads the telegraph; punishing if he is caught on the floor mid-charge.

## Work Completed

### Gameplay / systems touched

- Level flow: `LevelState(game, level_index)`. Results lead to the next level; after 1-4 the results say WORLD CLEAR and return to the title. Restart keeps the current level.
- Movement: vine swing (pendulum with pump, damping, angle clamp, scenery stop, regrab cooldown). Crouch hitbox while rolling, crawl under low ceilings, stand-up headroom check.
- Bug fix (pre-existing): roll presses were dropped about 3 frames in 4. Ground contact flickers while standing because gravity is skipped when grounded, so `on_ground` is true only every few frames. Jump already hid this with its buffer and coyote time; roll now uses the same (`PLAYER_ROLL_BUFFER` 0.12 s, coyote-timed). The underlying flicker is left as is (see risks).
- Enemies: `Enemy` gained a contact contract (`harmful`, `on_stomp`, `on_roll`, `STOMP_BOUNCE`). Snapper and Hopper behave as before. King Saurus implemented (was a stub).
- Collectibles: `GoalTotem(requires_boss=...)` stays hidden and untouchable until no boss is left.
- Loader / builder: `vine` objects (anchor + `length`), `requires_boss` totem property, and generic solid rectangles (`solids`) for logs, steps, walls and ledges.

### Files created

- `ape_escape/entities/props/__init__.py`, `ape_escape/entities/props/vine.py`
- `ape_escape/levels/tangle_jungle/1_2_vine_valley.tmx`, `1_3_hollow_log_run.tmx`, `1_4_saurian_arena.tmx` (generated by `tools/build_levels.py`)
- `tests/playthrough.py` (scripted-run harness and per-level scripts), `tests/test_levels.py`
- `docs/placeholder-art.md`
- this report

### Files modified

- `ape_escape/core/constants.py`, `ape_escape/core/states.py`, `ape_escape/entities/player.py`, `ape_escape/entities/enemies/enemy.py`, `ape_escape/entities/enemies/king_saurus.py`, `ape_escape/entities/collectibles/goal_totem.py`, `ape_escape/levels/tilemap.py`, `tools/build_levels.py`
- `smoke_test_adventure.py` (phase 3: load and step 1-2, 1-3, 1-4; check the results chain)
- `smoke_test.py`: it imported `ape_escape` (now the new package) and crashed on master before this session; it now imports `legacy_game` and passes. `legacy_game.py` is untouched.
- `docs/ARCHITECTURE.md` (props row), `docs/ROADMAP.md` (levels and arena ticked, boss marked first pass)

## Validation

- How completability was verified: `tests/playthrough.py` drives the real `LevelState` (real physics, enemies, vines, boss, totem) at a fixed 60 fps step with input scripts that react to live state, like a player. A run passes only on reaching `ResultsState` without dying. Results:
  - 1-1: completed, 13.7 s game time, 0 hits, 0 deaths
  - 1-2: completed, 18.0 s, 0 hits, 0 deaths (all 5 vines used)
  - 1-3: completed, 16.7 s, 0 hits, 0 deaths (all 4 logs rolled through)
  - 1-4: completed, 11.8 s, 0 hits, 0 deaths (3 stomps, totem revealed)
- Mechanic-required checks: a full running jump at gap A without the vine falls in; walking and jumping into log 1 never gets through; a roll fits under the log and crawls out; the 1-4 totem stays locked while the boss lives; roll and undazed stomps do not damage the boss.
- Progression: a full back-to-back run 1-1 -> 1-4 following each `ResultsState`, ending at `TitleState`.
- Commands (run serially): `py -m compileall -q ape_escape ape_escape.py smoke_test_adventure.py tests tools` clean; `py -m unittest discover -s tests -t .` 34 tests OK (19 existing + 15 new), about 7 s; `py -X faulthandler smoke_test_adventure.py` OK; `py smoke_test.py` OK; `py -m tests.playthrough` 4/4 completed.
- Screenshots: rendered mid-swing (1-2), mid-tunnel (1-3) and boss dazed (1-4); all read clearly.
- Not verified: a hands-on keyboard playtest, a 4-second GIF, and frame rate on the target laptop. Letter reachability is designed but not scripted (the runs collect 1-2 letters per level on the main route).

## Feel and Stability Notes

- Swing: from rest a release at about 0.8 rad carries the player about 6 tiles past the anchor. Release adds -300 px/s upward. Air control then caps horizontal speed at run speed, so the vine mostly buys height and hang time.
- Crawl speed is 110 px/s; chaining rolls is faster and feels better through long logs.
- Performance: vines draw about 13 line segments each; the boss is a handful of primitives. No per-frame surface allocation added. Low risk.

## Asset Notes

- No image files added. All new visuals are procedural PLACEHOLDER art, listed in `docs/placeholder-art.md` for sign-off.

## Tasks

### Open / remaining

- [ ] Hands-on keyboard playtest of 1-2 to 1-4 and a GIF for the PR #task #next [project:: Ape Adventure]
- [ ] Sign off the placeholder list in docs/placeholder-art.md #task [project:: Ape Adventure]
- [ ] King Saurus phases 2-3 per GAME_DESIGN.md (coconut bombs, stage hazard) #task [project:: Ape Adventure]
- [ ] Log tile type so hollow logs look like wood #task [project:: Ape Adventure]
- [ ] Checkpoints for the longer levels (none yet, as in 1-1) #task [project:: Ape Adventure]
- [ ] Decide whether to fix the ground-contact flicker at the root (apply gravity every frame) #task [project:: Ape Adventure]

## Blockers and Risks

- Ground-contact flicker (pre-existing): `on_ground` is true only every few frames while standing. Jump and now roll are buffered around it. Any future edge-triggered grounded action needs the same treatment, or the root fix.
- Slinger, Spike and Banana Bunch are still stubs and are not placed in any level.
- Boss music key `king_saurus` is set, but `AudioManager` plays one generated loop for every level.

## Handoff for Future Agents

- Edit levels in `tools/build_levels.py`, then run `py tools/build_levels.py`. Do not hand-edit the `.tmx` files unless moving to Tiled for good.
- After a level edit, run `py -m tests.playthrough <id> --trace` to see where a script breaks; scripts live in `tests/playthrough.py`.
- Keep enemies clear of vine take-offs and of the space under low platforms, or players get bounced into gaps or pinned under ceilings.
