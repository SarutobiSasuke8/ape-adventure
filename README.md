# Ape Adventure

> **Run. Roll. Rescue.**

A 90s-style jungle platformer where one ape takes on a Saurian invasion. Built in Python with pygame, inspired by SNES-era console platformers — original characters, original IP, painted look, soundtrack-led.

This repo contains:

- **`ape_adventure/`** — the new game (in active development; vertical slice in progress)
- **`ape_escape.py`** — the legacy v0 single-file arcade game (parked, still playable)

---

## Status

**Vertical slice in progress.** Target: 1 world (Tangle Jungle), 4 levels, 1 boss, ~6–8 weeks of work. The package currently has the **scaffold and an architecture-shaped stub** — running it opens a placeholder title screen.

For the full feature list of what's coming, see [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Quick start

### Run the new game (scaffold; placeholder title)

```bash
pip install -r requirements.txt
python -m ape_adventure
```

Requires Python 3.10+.

### Run the legacy v0 game (fully playable arcade game)

```bash
python ape_escape.py
```

---

## Project layout

```
Ape Adventure/
├── ape_adventure/         # NEW — multi-file pygame package
│   ├── __main__.py
│   ├── core/              # game loop, state machine, input, camera, physics
│   ├── entities/          # player, enemies, collectibles, hazards
│   ├── levels/            # tilemap loader, world data, .tmx files
│   ├── render/            # parallax, particles, HUD, palette
│   ├── audio/             # music + SFX manager
│   └── assets/            # sprites, tilesets, music, sfx (binary)
├── docs/
│   ├── GAME_DESIGN.md     # design pillars, mechanics, vertical slice spec
│   ├── ROADMAP.md         # vertical slice milestones + Stage 2 path
│   └── ARCHITECTURE.md    # package structure, module responsibilities
├── marketing/             # brand, strategy, launch, channels playbooks
├── ape_escape.py          # LEGACY v0 — single-file arcade game (parked)
├── ape_escape_highscore.json
├── smoke_test.py          # legacy smoke test for v0
├── CLAUDE.md              # working agreement for AI collaborators
├── AGENTS.md
├── LICENSE
├── requirements.txt
└── README.md
```

---

## Direction

*Ape Adventure* is a fresh project pivoting away from the legacy v0 (a single-file arcade homage). The new direction is a **side-scrolling 90s console platformer** — multi-world, hand-crafted levels, painted backdrops, real soundtrack. We're inspired by *Donkey Kong Country* and *Yoshi's Island* but everything in this game is original IP.

For the design treatment, see [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md).

---

## Controls (vertical slice target)

| Action | Keys |
|---|---|
| Move | `←` / `→` or `A` / `D` |
| Jump (variable height) | `Space` or `Z` |
| Run | Hold `Shift` |
| Roll attack | `X` or `Shift`-tap |
| Pause / Confirm | `Enter` / `P` |
| Back / Quit | `Esc` |

Gamepad support planned for the slice launch.

---

## Tech stack

- **Language:** Python 3.10+
- **Engine:** pygame 2.5+
- **Level authoring:** [Tiled](https://www.mapeditor.org/) (`.tmx`)
- **Level loading:** `pytmx`
- **Audio:** real `.ogg` music + `.wav` SFX (assets pending)
- **Persistence:** JSON save in OS-appropriate user data dir

---

## Working agreement

If you're contributing (human or AI), read [CLAUDE.md](CLAUDE.md) first. Key points:

- Multi-file package; modules have one responsibility
- Sprite + tilemap based; assets live under `ape_adventure/assets/`
- Original IP only — no Nintendo / *DKC* trademarks
- Don't break the legacy `ape_escape.py`

---

## License

MIT for the engine code — see [LICENSE](LICENSE). Asset licensing handled per-asset; see `marketing/launch/press-kit.md` for details when assets land.
