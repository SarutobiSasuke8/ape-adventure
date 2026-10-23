# Placeholder Art Register

Every piece of art in this list is a stand-in, waiting for Alexei's sign-off or replacement with final art. Add to it whenever new placeholder art lands.

Rule for image files: any placeholder image file must use the `PLACEHOLDER_` filename prefix and be listed here.

## Image files

| File | Added | Used by | Status |
|---|---|---|---|
| (none added for levels 1-2 to 1-4) | 2026-10-23 | | |

No new image files were added for levels 1-2, 1-3 and 1-4. They reuse the existing procedural tile renderer, parallax background, Bongo, Snapper, Hopper, banana, AAPE letter and goal totem drawings.

The existing `ape_escape/assets/tilesets/jungle_placeholder.png` (32x32 flat tile) predates this register. The runtime never loads it; it only lets Tiled open the `.tmx` maps.

## Procedural (code-drawn) placeholder art

These are drawn with `pygame.draw` calls in code, so there is no file to rename. Each module's docstring says PLACEHOLDER.

| Visual | Where | Added | Notes for final art |
|---|---|---|---|
| Vine (swing rope) | `ape_escape/entities/props/vine.py`, `Vine.draw` | 2026-10-23 | Segmented green line with leaf nubs, brown anchor knot, leafy grip. Final: hanging liana sprite with a sway animation and a hand-grip pose |
| Bongo swing pose (arms to grip) | `ape_escape/entities/player.py`, `Player.draw` | 2026-10-23 | Two fur-coloured lines from shoulders to grip. Final: swing frames in the Bongo sheet |
| Bongo crawl pose | `ape_escape/entities/player.py`, `Player.draw` | 2026-10-23 | Reuses the roll ball shape with an eye at the leading edge. Final: crawl/duck frames |
| King Saurus (boss) | `ape_escape/entities/enemies/king_saurus.py`, `KingSaurus.draw` | 2026-10-23 | Vector lizard with crown, tail, phase tint (green, olive, red), white hurt flash, spinning dazed stars, HP pips. Final: boss sprite sheet (telegraph, charge, crash, dazed, hurt, defeat) |
| Hollow logs | `ape_escape/render/renderer.py` (generic solid tiles) | 2026-10-23 | Logs in 1-3 are ordinary solid tiles, so they look like jungle earth, not wood. Final: a log tile type with bark, hollow mouth and inner shadow |
| Arena walls and ledges | `ape_escape/render/renderer.py` (generic solid tiles) | 2026-10-23 | Same generic tiles. Final: wooden arena palisade per GAME_DESIGN.md |

## Sign-off

- [ ] Alexei: placeholder list for levels 1-2 to 1-4 reviewed #task
