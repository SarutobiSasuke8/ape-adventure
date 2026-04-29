# CLAUDE.md — Ape Adventure Working Agreement

Working agreement for Claude Code (and other AI collaborators) on **Ape Adventure** — a 90s-era jungle-platformer homage built in Python with pygame.

This file replaces the previous arcade-game agreement (preserved alongside `legacy_game.py`, the legacy v0). The new direction is a side-scrolling adventure inspired by 1990s console platformers — multi-level worlds, lush biomes, collectibles, vehicles (later), boss fights.

---

## What this project is now

A 90s-style **side-scrolling platformer** with rich animation, real music, and a multi-world structure. Built in Python with pygame, structured as a **proper package** (no longer single-file).

**Direction:** *Donkey Kong Country–inspired* — but original characters, original IP, original art. Inspired by the genre, not a clone.

**Tone:** adventurous, warm, vivid. Emotional opposite of the legacy arcade game (which was dry and tense).

**Scope (current commitment):** **vertical slice** — 1 world ("Tangle Jungle"), 3–4 levels, 1 boss, 1 playable character. Architecture left open for a full DKC-style homage later (6 worlds, 30+ levels, tag-team characters, vehicles).

---

## What's in the repo

```
Ape Adventure/
├── ape_escape/         # NEW — the new game (multi-file package)
├── docs/                  # rewritten for the new direction
├── marketing/             # rewritten for the new brand
├── ape_escape.py          # ← launcher (run this to play)
├── legacy_game.py         # LEGACY v0 — keep playable, do not break
├── ape_escape_highscore.json   # legacy save — do not delete
├── smoke_test.py          # legacy smoke test for v0
├── README.md
└── CLAUDE.md              # (this file)
```

### Legacy game (`legacy_game.py`)

The single-file climbing-platformer is **parked, not deleted**. It still runs. Treat it as a finished v0 reference — do not modify, refactor, or delete it without explicit permission. New work happens under `ape_escape/`.

---

## Core principles (new)

1. **Multi-file is fine, but stay disciplined.** Each module has one responsibility. If a file grows past ~500 lines, propose a split. No god-objects.
2. **Assets are allowed.** Sprites, tilemaps, music, sound effects — all live under `ape_escape/assets/`. Use `.ogg` for music, `.wav` for short SFX, `.png` for sprites.
3. **Pygame-first.** New dependencies are allowed but each one must justify itself. Currently approved: `pygame`, `pytmx` (Tiled tilemap loader). Anything else, ask first.
4. **Lush 90s console look.** Pre-rendered-style sprites, parallax backgrounds, painted color palettes. **Not** retro pixel art (sharp 8-bit). **Not** flat vector. Aim for the *DKC-era SNES* feel: detailed, warm, atmospheric.
5. **Music matters.** A 90s platformer lives or dies on its soundtrack. Place real `.ogg` tracks in `assets/music/`. Synthesized loops are acceptable as placeholders only.
6. **60fps target on a modest laptop.** Profile if you add anything heavy (large particle systems, per-pixel effects). Tilemaps should be pre-rendered to a surface, not redrawn from scratch every frame.

---

## Code style

- Python **3.10+** (we want `match` / structural pattern, walrus, modern type hints).
- Top-level constants in `SCREAMING_SNAKE_CASE`, in `ape_escape/core/constants.py`.
- Classes for entities (`Player`, `Enemy`, `Collectible`, etc.).
- `update(dt, ...)` and `draw(surf, camera)` on every drawable entity. Entities never query input directly — `Player` reads from a passed-in input snapshot.
- Type annotations welcome where they aid clarity, not as decoration.
- One-line comments only on public-ish methods; docstrings on classes if the purpose isn't obvious from the name.

---

## Package layout (target)

```
ape_escape/
├── __init__.py
├── __main__.py             # entry: python ape_escape.py
├── core/                   # game loop, state machine, camera, physics
├── entities/               # Player, Enemy, Collectible, Hazard subclasses
├── levels/                 # Level loader, tilemap rendering, world data
├── render/                 # parallax, particles, HUD, transitions
├── audio/                  # music + SFX manager
├── assets/                 # sprites, tilemaps, music, sfx (binary files)
└── data/                   # save files, settings (text/JSON)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown.

---

## Visual rules

- **Sprite-based** for characters, enemies, collectibles, interactive objects.
- **Tile-based** for level geometry. Use Tiled (`.tmx`) authored maps loaded via `pytmx`. Tile size: 32×32.
- **Parallax** backgrounds with at least 2 layers (sky + middle ground) per world.
- **Saturated, painterly palette** — see `marketing/brand/visuals.md`.
- Subtle effects: leaf particles, water shimmer, light god-rays. **No** screen-warp, **no** rainbow flashes.

## Audio rules

- Music: looping `.ogg` per world (jungle theme, boss theme, title theme).
- SFX: `.wav` short clips. Hand-recorded, royalty-free, or commissioned. Synthesized fallback acceptable as placeholder.
- Volume: music ducked under SFX. Master mixer with persisted user volume.

---

## When making changes

- After any code change in `ape_escape/`: run `python ape_escape.py` and verify the title screen loads and the player can complete level 1.
- Run `python -m py_compile $(find ape_escape -name "*.py")` — must compile clean.
- For visual changes: capture a 4-second GIF of the change in motion and attach to the PR description.
- Never break the legacy `legacy_game.py`. Run `python legacy_game.py` once before declaring a task done if you touched any shared file (there shouldn't be any, but check).

---

## Session logging

Use the session-report flow from:

`C:\Users\sarut\Documents\Games Development Hub\cryptic-grove\Session Reports\Session Report Template.md`

For this game, follow the local game-dev adaptation in [docs/SESSION_REPORTING.md](docs/SESSION_REPORTING.md).

At the end of any meaningful build, debugging, art, audio, design, or release session, create or update a report under `Session Reports/` using:

`yyyy-mm-dd-session-report-ape-adventure.md`

The report should capture:

- Objective and outcome status.
- Gameplay loop or feature area touched.
- Files created or modified.
- Mechanics changed, removed, renamed, or intentionally left untouched.
- Validation run, including compile, smoke tests, and manual playtest notes.
- Feel notes: movement, camera, collision, enemy behavior, readability, pacing.
- Frame-rate or stability risks, especially particles, per-frame allocations, large blits, audio loading, or tilemap rendering.
- Asset notes: source, license, placeholder/final status, PixelLab or other generation IDs if used.
- Immediate next actions for the next coding agent.

Do not treat the report as a substitute for code comments or commit messages. It is a handoff document for future agents and humans.

---

## What to **not** do without asking

- Do not modify or delete `legacy_game.py` or `ape_escape_highscore.json`.
- Do not add online features, accounts, telemetry, or analytics.
- Do not add real-money mechanics, NFTs, ads, or wallet integration.
- Do not add a new dependency outside the approved list (`pygame`, `pytmx`).
- Do not change the title "Ape Adventure" without explicit confirmation.
- Do not use any Nintendo / Donkey Kong trademarked names, characters, or marks. Inspiration only — original IP only.

---

## Naming / IP

This is **original IP inspired by the genre**, not a clone or fan game.

- Hero ape: working name **Bongo** (rename pending — placeholder)
- Antagonist faction: **Saurians** (lizard people — original)
- Boss: **King Saurus** (placeholder)
- World 1: **Tangle Jungle**

Do not use: Donkey, Diddy, Kong, Kremling, K. Rool, banana coins, KONG letters (use **AAPE letters** instead), Wrinkly, Funky, Cranky, Candy, Animal Buddy specific names.

---

## Roadmap reference

- [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md) — design pillars, vertical slice spec, mechanics
- [docs/ROADMAP.md](docs/ROADMAP.md) — vertical slice milestones + path to full game
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — package structure and module responsibilities
