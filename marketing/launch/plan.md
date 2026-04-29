# Launch Plan

Two distinct launches:

1. **Vertical Slice launch** (~end of week 8 of dev) — free playable build of World 1
2. **Stage 2 / Full Game launch** (deferred ~6–12 months) — only if vertical slice traction warrants

This document focuses on **launch #1**. We'll write a fresh plan for #2 once we know if there's demand.

---

## Vertical Slice — launch goal

> **3,000 itch.io page visits, 500 GitHub stars, 200 wishlists (if Steam page is up) in the first 14 days.**

Stretch: getting the soundtrack sampled / reposted by a game-music YouTuber.

## Channels (priority order)

1. **itch.io** — playable build, devlog, "name your price"
2. **GitHub** — source for the open scaffold; star magnet
3. **YouTube** — 90-second gameplay trailer + a separate music-only video
4. **Hacker News** — Show HN post, single shot
5. **r/IndieGaming + r/pygame + r/snes** — three different framing angles
6. **Twitter / Mastodon / Bluesky** — clip drip campaign
7. **itch.io front-page submission**

## Pre-launch timeline (8 weeks of dev → 2 weeks of launch ramp)

### T-21 to T-14 — Pre-launch foundation (after dev wraps)
- [ ] Lock the build. Tag `v0.1.0-slice`.
- [ ] Write itch.io page copy in the new voice (`marketing/brand/voice.md`)
- [ ] Capture 8 hero screenshots (title, each level, boss, results screen)
- [ ] Build a **90-second gameplay trailer** (with music)
- [ ] Build a **separate music-only YouTube video** for the soundtrack (still gameplay imagery, unedited)
- [ ] Build a 6-second hero GIF (a roll attack into a Saurian smash)
- [ ] Render a static title-card image at 1920×1080
- [ ] Write the launch tweet (1 sentence + GIF + link)
- [ ] Write the HN post body (template below)
- [ ] Write 3 devlog posts (drafts) — one per launch-week day

### T-14 to T-7 — Soft launch
- [ ] Publish itch.io page (still unlisted; share with 5 trusted playtesters)
- [ ] Fix the bugs your testers find
- [ ] Schedule the social clip drip (3 clips, 2 days apart)

### T-7 to T-0 — Pre-launch buildup
- [ ] Day -7: First clip drop. "*Ape Adventure* — Tangle Jungle is open next Wednesday."
- [ ] Day -5: Second clip drop. Boss tease (silhouette only).
- [ ] Day -3: Third clip drop. Music sample.
- [ ] Day -2: Itch.io page goes public, no announcement yet
- [ ] Day -1: Final pass on README, repo description, social bios
- [ ] Day -1: Schedule HN, Reddit, Twitter posts for 09:00 PT day 0

### T-0 — Launch day
- [ ] **08:00 PT** — itch.io public, GitHub repo description finalized
- [ ] **09:00 PT** — Tweet/Mastodon/Bluesky launch post (clip + tagline + link)
- [ ] **09:30 PT** — Show HN post
- [ ] **10:00 PT** — r/IndieGaming post (focus on the painted look)
- [ ] **11:00 PT** — r/pygame post (focus on the architecture / build)
- [ ] **12:00 PT** — r/snes post (focus on the 90s-feel)
- [ ] **15:00 PT** — Music-only YouTube video goes live + crosspost link
- [ ] **Evening** — devlog post #1 ("Why a 90s-style platformer in 2026?")
- [ ] Reply to *every* comment for the first 24 hours

### T+1 to T+14 — Sustain
- [ ] Day +2: devlog #2 ("How Tangle Jungle was built — Tiled to pygame")
- [ ] Day +4: Lobste.rs post
- [ ] Day +7: 7-day metrics post (transparent numbers, in `marketing/voice`)
- [ ] Day +10: devlog #3 ("Music in *Ape Adventure* — composing for a level you can replay")
- [ ] Day +14: Retrospective post. Decide on Stage 2.

## Show HN post template

> **Title:** Show HN: A 90s-style jungle platformer in pygame, vertical slice playable
>
> **Body:**
> Hi HN — *Ape Adventure* is a 90s-style platformer I'm building in Python with pygame. After 8 weeks of work, the vertical slice is playable: 1 world (Tangle Jungle), 4 levels including a boss, ~30 minutes of game.
>
> It's an original-IP love letter to 1990s console platformers — painted backdrops, real soundtrack, momentum-led platforming. Not a fan game; not pixel-art retro; not a clone of any specific title.
>
> I'm sharing the slice now to find out if the feel is working before I commit to the full 6-world version. Source is open. The repo also includes my prior single-file pygame project (legacy v0) for the curious.
>
> - Itch.io: [URL]
> - Source: [URL]
> - Trailer: [URL]
> - Music-only video: [URL]
>
> MIT licensed. Happy to talk pygame architecture, level loading via Tiled + pytmx, or how I sourced the soundtrack.

## itch.io page hierarchy

1. Title-card hero image (1920×620)
2. Tagline: "**Run. Roll. Rescue.**"
3. Two-line pitch: *A 90s-style jungle platformer with painted backdrops and a soundtrack worth replaying. World 1: Tangle Jungle is playable now.*
4. 90-second trailer (embedded)
5. Three screenshots
6. "What's in the slice" — exact list (1 world, 4 levels, 1 boss, ~30 min)
7. "What's coming" — link to roadmap
8. Controls
9. How to run / download
10. Source link → GitHub
11. "Name your price" — default $0

## Risks

| Risk | Mitigation |
|---|---|
| HN post sinks | One-shot only — don't repost. Pivot to Lobste.rs and Reddit |
| Itch.io page rejected for IP | We're original IP. Be ready to clarify if any review flags it |
| First-time-Python-users can't run it | Ship a Windows exe via PyInstaller in the GitHub release |
| Performance regression on launch | Run smoke test + 30-min playthrough on Windows / macOS / Linux before tagging v0.1.0 |
| Music isn't good enough | Worst-case, ship slice without final score and honest about it. Better than fake hype |
| Audience confuses us with *DKC* | Lead all copy with "original IP" and "inspired by" — never invoke trademarked names |
| Slice doesn't feel good | Don't launch. Slip the date. Better to ship late than to ship a flat first impression |

## What we will *not* do at launch

- Pre-orders or any payment funnel
- "Wishlist now!" pressure outside the Steam-store-page workflow
- Reach out to streamers / press cold (they should find it because it's good, not because we begged)
- Accept any sponsored / paid promotion offer
- Make any claim we can't back up with the build
