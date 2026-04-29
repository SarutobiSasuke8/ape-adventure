# Game Design — Ape Adventure

A 90s-era jungle-platformer inspired by *Donkey Kong Country*. Original characters, original IP. Built in Python with pygame.

---

## Pillars

1. **Momentum is the music.** Run, roll, jump, swing — flow is the feel. Stopping should feel like a choice, never a punishment.
2. **The jungle is alive.** Foreground vines move. Birds startle when you sprint past. Water shimmers. The world reacts; the player notices.
3. **Risk is rewarded with secrets.** A bonus barrel hidden behind a waterfall. A hidden cave under a slope. Rewards exploration without forcing it.
4. **Death is fast, restart is faster.** No long animations on hit. ~1 second from death to back-in-control.
5. **Sound carries the mood.** A 90s platformer is its soundtrack. Each world is a song.

---

## Vertical slice — what we're shipping first

**1 world, 4 levels, 1 boss, 1 character.** Goal: prove the feel works end-to-end before scaling.

### World 1 — *Tangle Jungle*

The starting biome. Lush canopy, vines, swing ropes, hollow logs, a waterfall. Warm greens, dappled gold sunlight. Boss at the end is a Saurian chieftain in a wooden arena.

### Levels

| # | Name | Theme | Teaches | Length |
|---|---|---|---|---|
| 1-1 | **First Steps** | Open jungle path | Walk, jump, basic enemy | ~90s |
| 1-2 | **Vine Valley** | Canopy with swinging ropes | Rope swings, gap timing | ~2 min |
| 1-3 | **Hollow Log Run** | Cave-like log interiors | Roll attack, ducking, faster pacing | ~2 min |
| 1-4 | **The Saurian's Arena** | Boss room | Pattern read & punish | ~3 min (with retries) |

Each level ends with a goal totem. Touch it to clear; carry collected AAPE letters and bananas into a results screen.

---

## Core loop

```
Title → World map → Level start
  → run/jump/roll/swing → collect bananas, AAPE letters, hidden bonus barrels
    → reach the goal totem → results screen → next level
      → boss at end of world → world clear → credits (vertical slice)
```

Side loop: hit by enemy → die → respawn at last checkpoint → keep AAPE letters, lose bananas in current life.

---

## Mechanics — Hero (Bongo, working name)

### Movement
- **Walk:** ~140 px/s
- **Run:** ~240 px/s (hold run button after 0.4s of sustained input, or use sprint key)
- **Jump:** −520 px/s impulse, held jump = 30% extra height (variable jump)
- **Gravity:** 1500 px/s², terminal 1000 px/s
- **Coyote time:** 100ms
- **Jump buffer:** 120ms

### Actions
- **Roll attack** — quick forward dash that defeats most ground enemies and breaks crates. Brief invulnerability frames during roll.
- **Ground pound** (later) — defeats armored enemies; reveals hidden bonuses.
- **Rope swing** — grab vine, build momentum, release with jump.
- **Pick up & throw** (later) — barrels, coconuts, smaller enemies.

### Health
- Two-hit health. First hit drops Bongo to "stunned" state (palette flash, brief invuln). Second hit = death.
- Pickup: **banana bunch** restores one hit point (rare).

### Death rules
- Falls into pits = death (no second chance).
- Enemy contact while not rolling = lose health.
- Spike/hazard contact = death.

---

## Mechanics — Enemies (Saurian faction)

| Enemy | Behavior | Defeat |
|---|---|---|
| **Snapper** | Walks back and forth on a platform | Roll, jump, throw item |
| **Slinger** | Stationary, throws coconuts in arc | Roll while approaching, jump on head |
| **Spike-Back** | Walks; armored top — can only be defeated by ground pound or knock-back | Ground pound (later world); avoid in world 1 |
| **Hopper** | Hops along the ground; faster than Snapper | Time the jump on its peak |

Vertical slice ships **Snapper, Slinger, and Hopper** only. Spike-Back arrives with ground pound in a later world.

### Boss — King Saurus

Three-phase fight in a circular wooden arena.

- **Phase 1:** Charges horizontally; jump over him.
- **Phase 2:** Throws coconut bombs; dodge and counter-throw.
- **Phase 3:** Climbs onto a stage hazard and rains coconuts; ground-attack his feet by rolling into the stage supports.

Three hits total to defeat. Visual phase tells: color shift, posture change, music intensifies.

---

## Collectibles

| Item | Effect | Visibility |
|---|---|---|
| **Banana** | +1 banana count. 100 = extra life | Common; line them along skill paths |
| **Banana bunch** | +10 bananas, or +1 health if hurt | Rare |
| **AAPE letter** (A, A, P, E) | Collect all 4 in a level for an extra life + bonus reveal | One per level, hidden but discoverable |
| **Bonus barrel** | Hides a bonus room: a small skill challenge for bananas | 1–2 per level |
| **Goal totem** | Ends the level | One per level |

---

## Visual language

- **Style:** painted, layered, warm. Pre-rendered-style sprites (or AI-rendered placeholders during the slice). Multi-layer parallax skies. Color palette per world; world 1 is *jungle warm* — saturated greens, gold light, deep shade.
- **Animation budget:** 8-frame walk, 4-frame run, 4-frame jump, 6-frame roll, 4-frame idle (with breathing). Enemies get 4–6 frames each.
- **Effects:** leaf particles when running on grass, dust on landings, splash on water, glow on collectible pickups.
- **Camera:** smooth follow with a forward look-ahead (~80 px in run direction). Vertical clamping to keep ground visible.

---

## Audio

- **Music:** one main theme per world (`tangle_jungle.ogg`), one boss theme (`king_saurus.ogg`), one title theme. ~2-minute looping `.ogg` tracks. Atmosphere over melody — let it breathe.
- **SFX (vertical slice list):** jump, land, roll, hurt, defeat-enemy, pickup-banana, pickup-letter, pickup-bunch, goal-totem-touch, boss-hit, boss-defeated, level-clear, ui-confirm, ui-back.
- **Mixing:** music at -8 dB, SFX at -3 dB, with -6 dB duck on music when boss-hit / boss-defeated SFX play.

---

## UI

- **HUD (in-level):** banana count (top-left), AAPE letters (top-center, light up as collected), heart icons (top-right), pause hint (bottom-right corner, fade after 5s).
- **Pause menu:** Resume / Restart Level / Quit to World Map / Audio.
- **Results screen:** time, bananas collected, AAPE complete (Y/N), bonus barrels found (X/Y), continue button.
- **World map:** simple node graph. Locked levels visible but unselectable.
- **Title screen:** title art + "Press Start" + Options + Credits.

---

## What's deliberately **not** in the vertical slice

- A second playable character (e.g. tag-team).
- Vehicles (mine cart, barrel cannon).
- Swimming.
- Multiple worlds.
- Save slots beyond a single auto-save.
- Localization.
- Settings depth beyond audio sliders.

These are sequenced for the **full DKC homage** later — see `docs/ROADMAP.md`.

---

## Inspirations (for reference, not imitation)

- *Donkey Kong Country* (1994) — pacing, momentum, secrets, atmosphere
- *Yoshi's Island* (1995) — painterly look, generous platforming
- *Rayman Legends* (2013) — modern feel for old genre
- *Crash Bandicoot* (1996) — running-toward-camera energy in some screens

We are not making any of these games. We are paying attention to what made them feel good.
