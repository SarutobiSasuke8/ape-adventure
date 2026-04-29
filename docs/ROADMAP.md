# Roadmap — Ape Adventure

Two-stage roadmap. **Stage 1** is the vertical slice (~6–8 weeks). **Stage 2** is the optional path to a full *DKC*-style homage (~6–12 months) once Stage 1 ships and we know the core loop is fun.

---

## Stage 1 — Vertical Slice (target: 6–8 weeks)

A complete, playable proof of feel. 1 world, 4 levels, 1 boss, 1 character.

### Phase 1.1 — Foundation (Week 1)
- [ ] Scaffold `ape_adventure/` package per `docs/ARCHITECTURE.md`
- [ ] Game loop: window, fixed-timestep, FPS clamp
- [ ] State machine: TITLE → WORLD_MAP → LEVEL → PAUSE → RESULTS
- [ ] Input layer: keyboard + gamepad-ready abstraction
- [ ] Constants module + project config
- [ ] `python -m ape_adventure` runs and shows a placeholder title screen

### Phase 1.2 — Player & Physics (Week 2)
- [ ] Player class with walk/run/jump/coyote/jump-buffer
- [ ] Tilemap collision (axis-separated AABB)
- [ ] Camera with forward look-ahead and clamping
- [ ] Roll attack with i-frames
- [ ] Health system (2 HP, stunned state, death)
- [ ] Test level: a flat playground with platforms

### Phase 1.3 — Levels & Collectibles (Week 3)
- [ ] `pytmx` loader integration; load `world1_1.tmx`
- [ ] Goal totem (level end)
- [ ] Bananas, AAPE letters, banana bunches, bonus barrels
- [ ] Results screen with collection summary
- [ ] World map screen with level select (locked/unlocked)
- [ ] Persisted save (auto-save on level clear)

### Phase 1.4 — Enemies & Audio (Week 4)
- [ ] Snapper, Slinger, Hopper enemies
- [ ] Enemy/player damage exchange (roll defeats most, contact hurts)
- [ ] SFX manager + first SFX set (jump, land, roll, hurt, pickups)
- [ ] Music manager + placeholder jungle loop
- [ ] Hit-pause + screen shake on impacts (subtle)

### Phase 1.5 — Art & World Build (Weeks 5–6)
- [ ] Tangle Jungle tileset (32×32 tiles authored or AI-generated)
- [ ] Bongo sprite sheet (idle/walk/run/jump/roll/hurt/cheer)
- [ ] Enemy sprites (3 enemies, 4–6 frames each)
- [ ] Parallax sky for jungle
- [ ] Particle effects: dust, leaf, splash, sparkle
- [ ] Build levels 1-1 through 1-3 in Tiled

### Phase 1.6 — Boss & Polish (Weeks 7–8)
- [ ] King Saurus 3-phase boss fight
- [ ] Boss arena (1-4) build
- [ ] Boss music
- [ ] Title screen art
- [ ] World map art
- [ ] Pause menu finalized
- [ ] Final balance pass: timing, jump arcs, enemy speed
- [ ] Smoke test for the new package

### Phase 1.7 — Vertical slice ship (end of week 8)
- [ ] Build a Windows exe via PyInstaller
- [ ] Build a macOS bundle (if hardware available)
- [ ] Tag `v0.1.0-slice`
- [ ] Update marketing/launch/plan.md with vertical-slice launch date
- [ ] Show HN + itch.io publish (private/limited)

---

## Stage 2 — Full DKC Homage (deferred; only after Stage 1 ships and feels good)

This is the **door we left open**, not a commitment. After the vertical slice ships, decide whether to commit based on:
- Did the vertical slice feel good to play?
- Did anyone outside the team like it?
- Do we have 6 more months in us?

If yes:

### Stage 2.A — Second character (Tag-team, ~1 month)
- Diddy-style "Pip" (smaller, faster, lower jumps but glides briefly)
- Tag-swap mechanic; lose the active one first when hit
- Per-level "buddy barrel" mid-checkpoint that returns the lost partner

### Stage 2.B — World 2: *Coral Cove* (~1 month)
- New biome (beach + tide pools)
- Swimming mechanic
- 4 levels + boss

### Stage 2.C — World 3: *Cinder Caverns* (~1 month)
- Dark/lava biome
- Mine-cart vehicle level
- 4 levels + boss

### Stage 2.D — World 4: *Twisted Treetops* (~1 month)
- Verticality-focused; lots of rope/swing/wind
- Barrel-cannon vehicle level
- 4 levels + boss

### Stage 2.E — World 5: *Frostfern Reach* (~1 month)
- Snow biome; ice physics
- 4 levels + boss

### Stage 2.F — World 6: *Saurian Citadel* (final, ~1 month)
- Industrial/fortress
- Final multi-phase King Saurus rematch
- 6 levels + boss

### Stage 2.G — Final polish, ship 1.0 (~1 month)
- Save slots
- Speedrun timer toggle
- Photo mode
- Localization (English first, then community translations)

---

## Cut for now (deliberate non-goals — vertical slice)

- ❌ Online features, leaderboards, accounts, telemetry
- ❌ NFTs, ads, microtransactions
- ❌ Touch controls / mobile build
- ❌ Multiplayer (couch or online)
- ❌ Procedurally-generated levels
- ❌ Story cutscenes (vertical slice has none — boss intro is environmental)
- ❌ DLC plans

---

## Tech debt to track

(Empty for now — populate as new code is written and we make trade-offs.)

---

## Backlog (small ideas for later, not scheduled)

- [ ] Daily challenge level (same level, randomized enemy placement, leaderboard-free)
- [ ] Photo mode (pause + free camera + filters)
- [ ] Speedrun ghost (local only; race your last best)
- [ ] Charm/relic system (small passive modifiers found in bonus barrels)
- [ ] Hat cosmetics (no microtransactions; all earned in-game)
