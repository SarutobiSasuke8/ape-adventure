# AGENTS.md — Generic AI Agent Rules

For any AI agent (Codex, Cursor, Aider, Continue, etc.) contributing to
**Ape Escape**. Claude-specific guidance lives in [CLAUDE.md](CLAUDE.md);
treat that as authoritative if there's any conflict.

---

## Hard rules

1. **One file.** All gameplay code stays in `ape_escape.py`.
2. **pygame only.** No new dependencies in `requirements.txt`.
3. **No bundled assets.** No images, fonts, or audio files shipped.
4. **Compile clean.** `py -m py_compile ape_escape.py` must pass before
   handing back any change.
5. **No silent feature deletion.** If you remove or rename a mechanic, call
   it out clearly in your reply.

## Soft rules (defaults — override only with explicit instruction)

- Keep the existing palette and visual language. New colors go in the palette
  block at the top of the file.
- Keep the title text "APE ESCAPE" and the rescue text "HOW HIGH WILL YOU CLIMB?".
- Keep 60fps target, 3 lives, one-hit barrel deaths.
- Keep persistence in a single local JSON file.

## Workflow expectations

- Make small, reviewable changes — one mechanic or one polish pass at a time.
- After editing, mentally walk the game loop: title → start → climb → death →
  respawn → rescue → next level.
- Flag anything that *might* impact frame rate (particle counts, per-frame
  surface allocations, large blits).

## Out of scope

- Multiplayer, networking, accounts, leaderboards beyond local JSON.
- Real-money or wallet integrations.
- Pixel-art rendering, CRT shaders, or retro filters.
- Switching engines (Phaser, Godot, etc.) — this is and remains a pygame project.

See also: [README.md](README.md), [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md).
