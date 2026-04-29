# Visual Brand Guidelines

The look we're chasing: **a 1995 platformer cover painting come to life** — saturated, painted, warm, with depth in the shadows and gold in the highlights. This is the opposite of the legacy v0's vector minimalism.

## Core principle

> **Painted, warm, layered. Never pixel-art-retro, never flat-vector.**

If a screenshot could pass for a SNES cartridge cover from 1995, we're on track. If it looks like an asset flip or an 8-bit homage, we're off.

## Reference (mood, not imitation)

- *Donkey Kong Country 1–3* (1994–96) — the painted, pre-rendered look
- *Yoshi's Island* (1995) — the storybook palette and crayon-edge trees
- *Rayman Legends* (2013) — modern lush platformer art
- *Hollow Knight* (2017) — atmosphere and depth without high resolution

We are not imitating any one of these. We're aiming at the *family resemblance.*

## Color palette — Tangle Jungle (World 1)

Pulled directly from `ape_adventure/render/palette.py`. Source of truth lives in code; this file mirrors it for designers.

### Environment

| Name | Hex | Use |
|---|---|---|
| Jungle Deep | `#184026` | Deepest shadow, far parallax silhouette |
| Jungle Mid | `#306E3C` | Foreground foliage shadow |
| Jungle Light | `#82C054` | Sunlit leaves, grass tile tops |
| Canopy Gold | `#FAD25A` | Sun-shafts, accent glow |
| Wood Bark | `#60381E` | Tree trunks, log interior |
| Wood Light | `#A06E3C` | Branch highlights, exposed wood |
| Water Blue | `#3C8CBE` | Streams, waterfall mid-tone |
| Leaf Tint | `#A0E682` | Leaf particle accent |

### Cast & collectibles

| Name | Hex | Use |
|---|---|---|
| Bongo Fur | `#76462[6](mailto:6)` | Hero body |
| Bongo Light | `#AA7046` | Hero highlight |
| Banana Yellow | `#FFDC46` | Bananas, AAPE letter glow |
| Letter Gold | `#FAC83C` | Collected-letter glow |
| Saurian Green | `#5A823C` | Standard enemy body |
| Saurian Belly | `#DCC882` | Enemy underside |
| Saurian Red | `#B43C32` | King Saurus accent |

### UI

| Name | Hex | Use |
|---|---|---|
| Heart Full | `#DC3C46` | Health icon, full |
| Heart Empty | `#3C1E1E` | Health icon, depleted |
| HUD BG | `#0C0C12CC` | Translucent HUD strip |
| White | `#F5F7FA` | Body text |
| Black | `#0C0C12` | Title art, deep shadow |

> When World 2+ are added, each gets its own palette section here, sourced from `palette.py`.

## Typography

We don't ship fonts inside the game (system fonts are fine for HUD). For marketing materials outside the game:

- **Headlines:** A condensed, hand-drawn-feel display font with a slight texture. Free options: *Lilita One*, *Bowlby One*, *Luckiest Guy*.
- **Body:** -apple-system, "Segoe UI", Roboto, sans-serif (clean, neutral).
- **Numbers/scores in the game UI:** "Trebuchet MS" or any rounded sans — readable in motion.

## Logo / wordmark

The wordmark is **"APE ADVENTURE"** in a heavy, hand-drawn-feel display face with:
- A gold gradient (Canopy Gold → Banana Yellow)
- A jungle-green outer stroke (Jungle Mid)
- A subtle vine wrap on the "A" of *ADVENTURE*

When we need a static lockup:
1. Render once in vector (Affinity Designer / Illustrator), keep editable source in `marketing/assets/wordmark.afdesign` or `.svg`
2. Export at 1×, 2×, 4× resolutions

## Imagery rules

| Do | Don't |
|---|---|
| In-engine screenshots with full HUD | Cropped HUDs (the HUD is part of the brand) |
| Painted concept art for hero/enemy reveals | 3D renders or AI photorealism |
| 4–8 second loops of real gameplay | Edited "trailer cuts" with effects |
| Saturated, warm color grading | Desaturated, gritty, "moody" filters |
| Lush parallax visible in shots | Flat single-layer screenshots |
| Show the secret moments (bonus barrels, hidden paths) | Show only the main path |

## Motion

- 60fps capture, always.
- Loops 4–8 seconds.
- No transitions. Cuts only.
- Music in clips: yes, when the platform supports autoplay-with-sound (YouTube). Mute on Twitter/Bluesky/Mastodon by default — most autoplay is silent.

## Asset filename convention

```
ape-adventure__<context>__<descriptor>__<size>.<ext>
```

Examples:
- `ape-adventure__steam__hero__1920x620.png`
- `ape-adventure__twitter__roll-attack__1280x720.gif`
- `ape-adventure__itch__cover__630x500.png`
- `ape-adventure__presskit__bongo-portrait__2048x2048.png`

## Asset directory

When we start producing assets:

```
marketing/assets/
├── screenshots/       # 1920x1080 game captures
├── gifs/              # 1280x720, ≤8s loops
├── wordmark/          # SVG + PNG exports at 1×/2×/4×
├── concept/           # painted character/world art
└── presskit/          # the curated subset shipped to journalists
```
