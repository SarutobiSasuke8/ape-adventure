# Architecture — Ape Adventure

How the codebase is organized. The shape is chosen so that **vertical slice and full game share the same skeleton** — Stage 2 worlds drop into existing folders without restructuring.

---

## Top-level layout

```
ape_escape/
├── __init__.py           # version, package metadata
├── __main__.py           # entry: python ape_escape.py
├── core/                 # game loop, state machine, camera, physics, input
├── entities/             # Player, enemies, collectibles, hazards
├── levels/               # Level loader, tilemap rendering, world data
├── render/               # parallax, particles, HUD, transitions
├── audio/                # music + SFX manager
├── assets/               # sprites, tilemaps, music, sfx (binary)
└── data/                 # save files, settings (text/JSON)
```

The shape mirrors the data flow: **Input → Core → Entities/Levels → Render/Audio → Window**.

---

## Module responsibilities

### `core/`

| Module | Responsibility |
|---|---|
| `game.py` | Top-level `Game` class. Owns the state machine, the main loop, the active state |
| `states.py` | State classes: `TitleState`, `WorldMapState`, `LevelState`, `PauseState`, `ResultsState` |
| `input.py` | Read raw pygame events → publish a structured `InputSnapshot` per frame |
| `camera.py` | Smooth-follow camera with look-ahead and clamping to level bounds |
| `physics.py` | Axis-separated AABB collision against tile grid; gravity helpers |
| `constants.py` | All tunable constants. Screen size, FPS target, gravity, jump impulses, palette refs |

**Rule:** `core/` modules never import from `entities/` or `render/`. They define the framework; everything else plugs in.

### `entities/`

| Module | Responsibility |
|---|---|
| `entity.py` | Base `Entity` (rect, velocity, on_ground flag, update/draw signatures) |
| `player.py` | `Player` — Bongo. Reads `InputSnapshot`, runs locomotion + state machine |
| `enemies/` | One file per enemy: `snapper.py`, `slinger.py`, `hopper.py`. Inherit `Enemy` |
| `enemies/enemy.py` | Base `Enemy` with health, hit/defeat, patrol helpers |
| `enemies/king_saurus.py` | The boss — its own state machine for the 3 phases |
| `collectibles/` | `banana.py`, `aape_letter.py`, `bunch.py`, `bonus_barrel.py`, `goal_totem.py` |
| `hazards/` | `spike.py`, `pit.py` (most pits are tile-flagged, not entities) |

Every drawable entity exposes `update(dt, world)` and `draw(surf, camera)`. The `world` argument gives access to the level's tile grid + entity list.

### `levels/`

| Module | Responsibility |
|---|---|
| `level.py` | `Level` class: holds tile grid, entity list, parallax layers, music key, bounds |
| `tilemap.py` | `pytmx` loader; converts `.tmx` to a `TileGrid` plus entity spawn list |
| `world_data.py` | World/level metadata: names, music keys, unlock conditions |
| `<world>/<level>.tmx` | Authored levels (Tiled), e.g. `tangle_jungle/1_1_first_steps.tmx` |
| `<world>/tileset.tsx` | Tiled tileset (paired with PNG in assets/tilesets) |

### `render/`

| Module | Responsibility |
|---|---|
| `renderer.py` | Main draw orchestrator. Builds frame from layers (BG → tiles → entities → FX → HUD) |
| `parallax.py` | Multi-layer scrolling background |
| `particles.py` | Generic particle pool. Used for dust, leaf, sparkle, splash |
| `hud.py` | In-level HUD: bananas, AAPE letters, hearts, pause hint |
| `transitions.py` | Screen wipes between states (level→results, world map→level) |
| `palette.py` | Named color constants — single source of truth |

### `audio/`

| Module | Responsibility |
|---|---|
| `audio.py` | `AudioManager` — singleton-ish; loads music + sfx, ducking, volume |
| `tracks.py` | Track metadata: filenames, loop points, base volume |

### `assets/`

```
assets/
├── sprites/
│   ├── bongo/        # idle.png, walk.png, run.png, jump.png, roll.png, hurt.png, cheer.png
│   ├── enemies/      # snapper.png, slinger.png, hopper.png, king_saurus.png
│   ├── collectibles/ # banana.png, aape_letters.png, bunch.png, barrel.png, totem.png
│   └── ui/           # hearts.png, pause_hint.png, button_prompts.png
├── tilesets/
│   └── tangle_jungle.png
├── music/
│   ├── title.ogg
│   ├── tangle_jungle.ogg
│   └── king_saurus.ogg
└── sfx/
    ├── jump.wav, land.wav, roll.wav, hurt.wav, …
    └── ui_confirm.wav, ui_back.wav
```

### `data/`

Text-only; user-writable.

```
data/
├── save.json        # auto-save: progress, last level, AAPE collection
└── settings.json    # volume, key bindings, fullscreen
```

`data/` lives next to the package on first launch but **resolves to a user data dir** (`%APPDATA%/ApeAdventure` on Windows, `~/.local/share/ApeAdventure` on Linux, `~/Library/Application Support/ApeAdventure` on macOS) via a tiny helper in `core/paths.py`. Devs editing in-tree get a local fallback.

---

## State machine flow

```
[Boot]
  ↓
[TitleState] ── press start ──▶ [WorldMapState]
  ▲                                    │
  │                              select level
  │                                    ▼
  │                            [LevelState] ◀──┐
  │                                    │       │
  │                                 ┌──┴──┐    │
  │                                 │     │    │
  │                              clear   die  pause
  │                                 │     │    │
  │                                 ▼     │    ▼
  │                          [ResultsState]  [PauseState]
  │                                 │            │
  │                                 ▼            │
  └──── quit ─────────────── [WorldMapState] ◀───┘
```

Each state implements: `enter()`, `handle(input_snapshot)`, `update(dt)`, `draw(surf)`, `exit()`.

---

## Frame lifecycle

```
1. clock.tick(60)
2. events = pygame.event.get()
3. input_snapshot = Input.poll(events)
4. current_state.handle(input_snapshot)
5. current_state.update(dt)
6. current_state.draw(window_surface)
7. pygame.display.flip()
```

Transitions between states queue a `next_state` change applied at the top of step 4.

---

## Coordinate systems

- **World coords:** pixels in level space. Entities live here.
- **Camera coords:** world coords minus camera offset. Used by `draw()`.
- **Screen coords:** final pixel coords on the window. Used by HUD only.

The renderer handles the world→screen transform. Entities never compute screen coords themselves.

---

## Adding a new world (Stage 2 workflow)

When we're ready to add World 2:

1. Create `assets/tilesets/coral_cove.png` + Tiled tileset
2. Create `assets/sprites/enemies/<new enemies>`
3. Add tracks `assets/music/coral_cove.ogg` (+ boss theme)
4. Add level files under `levels/coral_cove/`
5. Add an entry to `levels/world_data.py`
6. Add new enemy classes under `entities/enemies/`
7. World 2 appears on the world map automatically once unlocked

No restructuring needed. That's the test of whether this architecture is right.

---

## What we're deliberately not building

- An entity-component system. Plain inheritance is enough at this scale.
- A scripting layer. Levels are data + tile properties, not scripts.
- A scene graph. The state machine + entity list is the scene.
- A custom build system. `python ape_escape.py` runs it; PyInstaller packages it.

If any of these become genuinely necessary, raise it as a question first.
