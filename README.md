# Ape Adventure

> **Run. Roll. Rescue.**

A 90s-style jungle platformer where one ape takes on a Saurian invasion. Built in Python with pygame, inspired by SNES-era console platformers — original characters, original IP, painted look, soundtrack-led.

This repo contains:

- **`ape_escape.py`** — run this to launch the game
- **`ape_escape/`** — the game package (multi-file, active development)
- **`legacy_game.py`** — the original v0 single-file arcade prototype (parked)

---

## Quick start

```bash
pip install -r requirements.txt
python ape_escape.py
```

Requires Python 3.10+.

---

## Local verify

Smoke test, one command (Python 3.10+, after `pip install -r requirements.txt`):

```bash
python smoke_test_adventure.py
```

It runs headlessly (dummy SDL video and audio drivers). It boots the real `Game`, presses Enter on the title screen and steps the frame loop into Tangle Jungle 1-1, then drives the level through movement, a death and respawn, and the goal totem into the results screen. It prints `Ape Adventure boot OK` and `Ape Adventure smoke test OK` and exits non-zero on any failure. Settings are redirected to a temp folder, so it does not touch your saved settings.

Unit tests:

```bash
python -m unittest discover -s tests -t .
```

GitHub Actions (`.github/workflows/ci.yml`) runs the compile check, the unit tests and the smoke test on Python 3.10 and 3.12 for every pull request and every push to `master`. It has no deploy step.

The parked v0 prototype has its own `python smoke_test.py`. It currently fails because its `import ape_escape` resolves to the active package, which has no `WIDTH` constant, so it is not part of CI.

---

## Status

**Vertical slice in progress** — World 1 (Tangle Jungle). Playable end-to-end today:

- ✅ Title screen → level → results screen flow
- ✅ Player: walk, run, jump (coyote time + jump buffer), roll attack, 2 HP
- ✅ Enemies: Snapper (patrol) + Hopper (hop AI)
- ✅ Collectibles: bananas, AAPE letters, goal totem
- ✅ Procedural jungle music loop + 9 SFX
- ✅ Screen shake + hit-pause on all impacts
- ✅ Save system (best time, bananas, AAPE per level)
- ✅ Particles: dust, leaves, sparkles, puff
- ✅ 3-layer parallax background, jungle tree silhouettes, hanging vines
- 🔲 Slinger enemy, boss fight, Tiled level loader, world map

For the full roadmap see [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Legacy v0

`legacy_game.py` is the original single-file arcade prototype — parked, not deleted. It still runs (`python legacy_game.py`) but is not under active development.

---

## Project layout

```
Ape Adventure/
├── ape_escape/         # NEW — multi-file pygame package
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
├── ape_escape.py          # ← RUN THIS to launch the game
├── legacy_game.py         # LEGACY v0 — original single-file prototype (parked)
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
| Start / Confirm | `Enter` |
| Pause menu (in a level) | `Esc` or `P` |
| Menu navigation | Arrows or `W` / `A` / `S` / `D`, `Enter` or `Space` to select |
| Quit (title screen) | `Esc` |

The pause menu offers Resume, Restart, Settings and Quit to title. Settings (music volume, SFX volume, reduced motion) are saved to `settings.json` in the per-user data folder: `%APPDATA%\ApeAdventure` on Windows, `~/Library/Application Support/ApeAdventure` on macOS, `$XDG_DATA_HOME/ApeAdventure` (default `~/.local/share/ApeAdventure`) on Linux. Reduced motion turns off screen shake and the title, results and HUD bobbing and blinking.

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
- Sprite + tilemap based; assets live under `ape_escape/assets/`
- Original IP only — no Nintendo / *DKC* trademarks
- Don't break the legacy `legacy_game.py`

---

## License

MIT for the engine code — see [LICENSE](LICENSE). Asset licensing handled per-asset; see `marketing/launch/press-kit.md` for details when assets land.
