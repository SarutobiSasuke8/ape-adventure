# Community Playbook

The plan is **small, slow, sustainable**. No Discord with 500 idle members. No "community manager." No engagement metrics that pretend to measure belonging.

## Philosophy

> A community is built on *replies*, not announcements.

We're hosting a small room for people who like the game and the craft, with us occasionally in the conversation. Not building a fanbase.

## Channels (in priority order)

### 1. GitHub Issues / Discussions — primary

**Why:** It's where the source lives. People who care enough to file an issue or open a discussion are the audience we want most.

**Cadence:** Reply within 48h. Tag aggressively (`bug`, `feel`, `feature`, `polish`, `question`, `art`, `music`). Close with kindness, even when declining.

**Rules:**
- Welcome every first-time contributor by name in their first comment
- Always explain *why* a feature is declined, with reference to `CLAUDE.md` principles or the roadmap stage
- Never close an issue with "won't fix" — write a real reason

### 2. Itch.io comments — secondary

**Why:** That's where casual players land.

**Cadence:** Check 2×/week minimum. Reply within 5 days.

**Rules:**
- Reply to every comment in the first month, even "cool!"
- After month 1, reply to anything with a question or feedback

### 3. Discord — *deferred*

**Decision:** Do **not** start a Discord at the vertical slice launch.

**Why:**
- A new Discord with 12 members feels worse than no Discord
- It demands daily presence, which we don't have
- The audience can find us on GitHub and itch

**Trigger to reconsider:**
- 500+ GitHub stars, OR
- 5+ unsolicited "is there a Discord?" requests in a single week, OR
- Stage 2 commitment is made

When that day comes, we'll write `community-discord.md` then.

### 4. Reddit — passive

**Why:** Watch r/IndieGaming, r/pygame, r/snes, r/gamemusic for organic mentions. Don't run a subreddit.

**Cadence:** Search weekly. Reply to direct mentions only.

## What we welcome

- Bug reports (with repro steps and OS info)
- Forks (especially playful ones — palette swaps, weird mechanic mods, "what if Bongo had wings")
- Speedrun videos
- Devlog inspiration ("I tried something similar, here's mine")
- Music remixes / arrangements (tag for moderation, default-positive)
- Fan art (default-positive, share to socials with credit and consent)
- Translation efforts (Stage 2+)

## What we deflect (gently)

- "When are you adding multiplayer?" → see `CLAUDE.md` non-goals; tag-team is Stage 2 candidate
- "Can you make a mobile version?" → not on the roadmap
- "Why don't you use [Unity / Godot / framework]?" → pygame fits the project; the constraint is part of the craft
- "Can you add NFTs / leaderboards / accounts?" → no, and here's why (link to CLAUDE.md non-goals)
- "Is this a *DKC* fan game?" → no, original IP — but DKC was an inspiration. Different characters, different worlds, different studio.

## Contributor expectations

For PRs, our `CONTRIBUTING.md` (to be written before public launch) will say:

- **Match the architecture** — see `docs/ARCHITECTURE.md` for module boundaries
- **No new dependencies** without prior issue / discussion
- **Run the smoke test and `python -m py_compile`** before submitting
- **Match the existing voice** in code comments (one-liners only)
- **For visual changes**, attach a before/after GIF
- **For audio contributions**, include the source `.wav`/`.ogg` and license/attribution
- **For new sprites**, include the source file (Aseprite, PSD, etc.) and matching exported PNG
- **No trademark-adjacent content** — we don't accept anything that references *DKC*-or-similar trademarks

## Code of conduct

Adopt the **Contributor Covenant 2.1** verbatim. Don't write our own. Add to `CODE_OF_CONDUCT.md` at root.

## Moderation principles

1. **Slow is fine.** Not every thread needs an instant reply.
2. **Public is preferred.** Default to public replies; DM only for sensitive matters.
3. **One warning, then a block.** No "three strikes" theatre.
4. **Tone over content.** A rude bug report is still a useful bug report. We just respond cool.
5. **IP vigilance.** Anything that drifts toward trademark territory gets a polite redirect to original-IP framing.

## What community success looks like

After 6 months post-slice launch, we'd love to see:
- 5–10 forks that did something genuinely creative
- 2–3 speedrun videos we didn't ask for
- A handful of contributors with multiple merged PRs
- A music remix or arrangement we can share
- One unsolicited piece of fan art

We would *not* love to see:
- 50 issues filed by the same person demanding features
- A Discord that requires a moderator schedule
- Drama, "discourse," or any thread longer than 30 replies
- Any conversation about NFTs, monetization, or "selling out"

## When the community goes quiet

A quiet period is not a problem. Vertical slice is finished. People will come back when they remember it, when they discover it, when someone they trust mentions it.

If 30 days pass with zero new engagement, ship a small visible improvement (a polish item from `docs/ROADMAP.md`) and post about it. Don't beg for attention.

## When the community gets loud

If a post takes off:
- Don't burn out replying to everyone
- Pin a single update with the most-asked questions answered
- Take a break after the wave passes — sustainability matters more than this week's metrics
- If "where's the full game?" becomes the loudest question, that's *the signal* — start Stage 2 planning
