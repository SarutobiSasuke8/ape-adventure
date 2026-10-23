"""Author Tangle Jungle levels as Tiled-compatible .tmx files.

This is a *level authoring* tool, not part of the runtime package. It builds
level geometry and entity placement as data, then emits a `.tmx` map that:

  * the in-game `pytmx` loader (`ape_escape/levels/tilemap.py`) reads back, and
  * a human can open and refine in Tiled later.

Run from the repo root:

    python tools/build_levels.py

TMX authoring contract (kept in sync with the loader):
  * Tile layer "collision": gid 1 = solid block, 0 = empty.
  * Object group "entities": every object names an entity via a "kind"
    property (and a mirrored `type`/class attribute). The object's (x, y) is
    the entity's **bottom-centre**, placed on a surface. Letters carry a
    "letter" property; bonus barrels a "sub_level_id".
  * Vines are the exception: (x, y) is the vine's *anchor* (top edge of the
    given row) and a "length" property gives the rope length in px.
  * A goal totem with "requires_boss" = "true" stays hidden until the boss
    is defeated (boss arenas).
  * A "checkpoint" is a respawn post. Touching it moves later respawns there.
  * "king_saurus" carries "arena_left" / "arena_right" in px (see loader).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
LEVELS_DIR = ROOT / "ape_escape" / "levels"
TILESETS_DIR = ROOT / "ape_escape" / "assets" / "tilesets"

TS = 32  # tile size (px)


@dataclass
class Spawn:
    """A single entity placement. (col, row) is the surface the entity rests on.

    x/y written to the .tmx are the entity's bottom-centre in pixels:
    bottom-centre lets the loader seat entities of any height on a surface.
    """
    kind: str
    col: float
    row: int               # the row whose *top* edge the entity stands on
    props: dict[str, str] = field(default_factory=dict)

    def pixel_xy(self) -> tuple[float, float]:
        return (self.col * TS + TS / 2.0, self.row * TS)


@dataclass
class LevelSpec:
    level_id: str
    name: str
    cols: int
    rows: int
    music_key: str
    ground_rows: tuple[int, ...]            # solid floor rows (full width minus pits)
    pits: tuple[tuple[int, int], ...]       # (col_lo, col_hi) inclusive gaps in the floor
    platforms: tuple[tuple[int, int, int], ...]  # (row, col_start, col_end_exclusive)
    spawns: list[Spawn]
    out_path: str                            # relative to LEVELS_DIR
    # Extra solid rectangles (col, row, cols, rows): walls, hollow logs, steps.
    solids: tuple[tuple[int, int, int, int], ...] = ()


def build_grid(spec: LevelSpec) -> list[list[int]]:
    grid = [[0] * spec.cols for _ in range(spec.rows)]
    for row in spec.ground_rows:
        for col in range(spec.cols):
            in_pit = any(lo <= col <= hi for lo, hi in spec.pits)
            if not in_pit:
                grid[row][col] = 1
    for row, c0, c1 in spec.platforms:
        for col in range(c0, c1):
            grid[row][col] = 1
    for col, row, cols, rows in spec.solids:
        for r in range(row, row + rows):
            for c in range(col, col + cols):
                grid[r][c] = 1
    return grid


def grid_to_csv(grid: list[list[int]]) -> str:
    # Tiled CSV: row-major, comma-separated, trailing comma except final value.
    flat = [str(cell) for row in grid for cell in row]
    return ",".join(flat)


def render_object(obj_id: int, spawn: Spawn) -> str:
    x, y = spawn.pixel_xy()
    props_xml = ""
    props = {"kind": spawn.kind, **spawn.props}
    prop_lines = "".join(
        f'   <property name="{escape(k)}" value="{escape(str(v))}"/>\n'
        for k, v in props.items()
    )
    props_xml = f"  <properties>\n{prop_lines}  </properties>\n"
    return (
        f' <object id="{obj_id}" type="{escape(spawn.kind)}" x="{x:g}" y="{y:g}">\n'
        f"{props_xml}"
        f"  <point/>\n"
        f" </object>\n"
    )


def render_tmx(spec: LevelSpec) -> str:
    grid = build_grid(spec)
    csv = grid_to_csv(grid)
    objects = "".join(render_object(i + 1, s) for i, s in enumerate(spec.spawns))
    next_object_id = len(spec.spawns) + 1
    # Relative path from the level's folder to the placeholder tileset image.
    depth = len(Path(spec.out_path).parent.parts)
    up = "../" * (depth + 2)  # +2: out of levels/ and ape_escape/... back to assets
    image_src = f"{up}ape_escape/assets/tilesets/jungle_placeholder.png"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" \
renderorder="right-down" width="{spec.cols}" height="{spec.rows}" \
tilewidth="{TS}" tileheight="{TS}" infinite="0" nextlayerid="3" \
nextobjectid="{next_object_id}">
 <properties>
  <property name="level_id" value="{escape(spec.level_id)}"/>
  <property name="name" value="{escape(spec.name)}"/>
  <property name="music_key" value="{escape(spec.music_key)}"/>
 </properties>
 <tileset firstgid="1" name="jungle" tilewidth="{TS}" tileheight="{TS}" \
tilecount="1" columns="1">
  <image source="{image_src}" width="{TS}" height="{TS}"/>
 </tileset>
 <layer id="1" name="collision" width="{spec.cols}" height="{spec.rows}">
  <data encoding="csv">
{csv}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
{objects} </objectgroup>
</map>
"""


def ensure_placeholder_tileset() -> None:
    """Write a tiny 32x32 placeholder PNG so Tiled can open the maps.

    The runtime never loads this image (tiles are drawn procedurally); it
    exists only so the .tmx is valid/editable in the Tiled editor.
    """
    png = TILESETS_DIR / "jungle_placeholder.png"
    if png.exists():
        return
    TILESETS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import pygame
        surf = pygame.Surface((TS, TS))
        surf.fill((46, 110, 58))
        pygame.draw.rect(surf, (30, 80, 46), surf.get_rect(), 2)
        pygame.image.save(surf, str(png))
    except Exception as exc:  # pygame missing or headless save issue — non-fatal
        print(f"  (skipped placeholder PNG: {exc})")


# ---------------------------------------------------------------------------
# Level 1-1 — "First Steps": a gentle teaching level.
# ---------------------------------------------------------------------------

def banana_arc(col_start: int, col_end: int, row: int, step: int = 2) -> list[Spawn]:
    return [Spawn("banana", c + 0.5, row) for c in range(col_start, col_end, step)]


def spec_1_1() -> LevelSpec:
    COLS, ROWS = 110, 18
    GROUND = 16  # surface row of the floor (rows 16-17 solid)
    spawns: list[Spawn] = []

    # Player start
    spawns.append(Spawn("spawn", 3, GROUND))

    # --- Platforms (row, col_start, col_end_exclusive) — low and forgiving ---
    platforms = (
        (13,  6, 12),
        (12, 16, 22),
        (13, 26, 31),
        (12, 44, 50),   # landing after pit 1
        (11, 56, 62),
        (13, 78, 84),   # landing after pit 2
        (12, 90, 96),
    )

    # --- Enemies: Snappers introduced first, one Hopper near the end ---
    spawns += [
        Spawn("snapper", 9,  13),    # on first platform
        Spawn("snapper", 28, 13),    # third platform
        Spawn("snapper", 47, 12),    # platform after pit 1
        Spawn("hopper",  92, 12),    # late platform — trickier read
        Spawn("snapper", 100, GROUND),  # ground, guarding the goal
    ]

    # --- Bananas: arcs guiding the player along the path ---
    spawns += banana_arc(4, 12, GROUND - 1)
    spawns += banana_arc(6, 12, 12)        # over first platform
    spawns += banana_arc(16, 22, 11)       # over second platform
    spawns += banana_arc(31, 44, GROUND - 1, step=3)
    spawns += banana_arc(56, 62, 10)       # reward for the high platform
    spawns += banana_arc(63, 78, GROUND - 1, step=3)
    spawns += banana_arc(96, 105, GROUND - 1)

    # --- AAPE letters: spread across the level, off the main path ---
    spawns += [
        Spawn("letter", 18, 11, {"letter": "A1"}),  # second platform crest
        Spawn("letter", 58, 10, {"letter": "A2"}),  # high platform
        Spawn("letter", 35, GROUND - 4, {"letter": "P"}),  # floating over ground gap area
        Spawn("letter", 81, 12, {"letter": "E"}),   # platform after pit 2
    ]

    # --- Goal totem ---
    spawns.append(Spawn("goal_totem", 106, GROUND))

    return LevelSpec(
        level_id="1-1",
        name="First Steps",
        cols=COLS,
        rows=ROWS,
        music_key="tangle_jungle",
        ground_rows=(GROUND, GROUND + 1),
        pits=((34, 36), (70, 72)),
        platforms=platforms,
        spawns=spawns,
        out_path="tangle_jungle/1_1_first_steps.tmx",
    )


# ---------------------------------------------------------------------------
# Level 1-2, "Vine Valley": introduces the vine swing.
#
# Four gaps are too wide to jump (8+ tiles; a full running jump clears about
# 5). Each has a vine. The first vine sits over a short drop with bananas
# tracing the swing, the last gap needs two vines in a row.
# ---------------------------------------------------------------------------

VINE_ROW = 9       # anchor row: the rope hangs from the top edge of row 9
VINE_LEN = 128     # 4 tiles


def vine(col: int, row: int = VINE_ROW, length: int = VINE_LEN) -> Spawn:
    return Spawn("vine", col, row, {"length": str(length)})


def spec_1_2() -> LevelSpec:
    COLS, ROWS = 130, 18
    GROUND = 16
    spawns: list[Spawn] = [Spawn("spawn", 3, GROUND)]

    pits = (
        (16, 23),    # gap A: first vine (teaching)
        (40, 47),    # gap B: vine, letter A2 at the top of the swing
        (56, 58),    # ordinary jump, a breather
        (64, 77),    # gap C: two vines back to back
        (96, 103),   # gap D: vine with a Hopper waiting on the far side
    )
    platforms = (
        (13, 28, 34),   # letter A1 perch
        (12, 86, 92),   # letter E perch, Snapper guard
    )

    spawns += [vine(18), vine(42), vine(66), vine(72), vine(98)]
    spawns.append(Spawn("checkpoint", 60, GROUND))   # mid-level, before gap C

    spawns += [
        Spawn("snapper", 8, GROUND),       # warm-up, same as 1-1
        Spawn("hopper", 31, GROUND),
        Spawn("snapper", 52, GROUND),
        Spawn("hopper", 83, GROUND),
        Spawn("snapper", 89, 12),          # on the E perch
        Spawn("hopper", 108, GROUND),      # right after gap D's landing
        Spawn("snapper", 116, GROUND),
    ]

    # Bananas trace each swing so the player reads the arc.
    spawns += banana_arc(4, 15, GROUND - 1)
    spawns += [Spawn("banana", c + 0.5, r) for c, r in ((18, 13), (20, 13), (22, 12), (24, 12))]
    spawns += banana_arc(26, 39, GROUND - 1, step=3)
    spawns += [Spawn("banana", c + 0.5, r) for c, r in ((42, 13), (44, 13), (47, 12))]
    spawns += banana_arc(49, 63, GROUND - 1, step=3)
    spawns += [Spawn("banana", c + 0.5, r) for c, r in ((66, 13), (68, 13), (72, 13), (74, 13), (77, 12))]
    spawns += banana_arc(79, 95, GROUND - 1, step=4)
    spawns += [Spawn("banana", c + 0.5, r) for c, r in ((98, 13), (100, 13), (103, 12))]
    spawns += banana_arc(105, 124, GROUND - 1, step=3)

    spawns += [
        Spawn("letter", 31, 12, {"letter": "A1"}),   # perch above the ground
        Spawn("letter", 45, 11, {"letter": "A2"}),   # top of the gap B swing
        Spawn("letter", 70, 11, {"letter": "P"}),    # between the twin vines
        Spawn("letter", 90, 11, {"letter": "E"}),    # perch with a Snapper
    ]
    spawns.append(Spawn("goal_totem", 125, GROUND))

    return LevelSpec(
        level_id="1-2",
        name="Vine Valley",
        cols=COLS,
        rows=ROWS,
        music_key="tangle_jungle",
        ground_rows=(GROUND, GROUND + 1),
        pits=pits,
        platforms=platforms,
        spawns=spawns,
        out_path="tangle_jungle/1_2_vine_valley.tmx",
    )


# ---------------------------------------------------------------------------
# Level 1-3, "Hollow Log Run": introduces rolling under hollow logs.
#
# A hollow log is a solid trunk (rows 12-14) over a one-tile tunnel (row 15).
# Bongo stands 44 px tall, so the only way through is to roll (24 px) and
# keep rolling or crawl. Its top is 128 px up, too high to jump. Later logs
# hide Snappers, so the roll is also the attack, and the pits grow to 4 tiles.
# ---------------------------------------------------------------------------

def hollow_log(col: int, length: int) -> tuple[int, int, int, int]:
    return (col, 12, length, 3)


def spec_1_3() -> LevelSpec:
    COLS, ROWS = 140, 18
    GROUND = 16
    TUNNEL = GROUND  # entities in a tunnel stand on the ground row
    spawns: list[Spawn] = [Spawn("spawn", 3, GROUND)]

    solids = (
        hollow_log(14, 6),     # log 1: empty, bananas show the way
        hollow_log(38, 10),    # log 2: one Snapper inside, letter A2
        (66, 14, 2, 2),        # step block: hop it, or take the high route onto log 3
        hollow_log(70, 10),    # log 3: tunnel below, letter P on top
        hollow_log(94, 12),    # log 4: two Snappers inside
    )
    pits = ((30, 33), (60, 63), (110, 113))
    platforms = (
        (13, 53, 58),    # letter A1 perch with a Snapper
        (12, 116, 121),  # letter E perch
    )

    spawns.append(Spawn("checkpoint", 64, GROUND))   # mid-level, after the second pit

    spawns += [
        Spawn("snapper", 25, GROUND),     # open-ground roll practice
        Spawn("snapper", 43, TUNNEL),     # inside log 2
        Spawn("hopper", 50, GROUND),
        Spawn("snapper", 55, 13),         # on the A1 perch
        Spawn("hopper", 84, GROUND),
        Spawn("snapper", 89, GROUND),
        Spawn("snapper", 98, TUNNEL),     # inside log 4
        Spawn("snapper", 103, TUNNEL),    # inside log 4
        Spawn("hopper", 119, 12),         # guarding the E perch
        Spawn("snapper", 127, GROUND),
    ]

    spawns += banana_arc(4, 13, GROUND - 1)
    spawns += banana_arc(14, 20, GROUND, step=2)          # inside log 1
    spawns += banana_arc(21, 30, GROUND - 1, step=3)
    spawns += banana_arc(34, 38, GROUND - 1, step=2)
    spawns += banana_arc(39, 48, GROUND, step=2)          # inside log 2
    spawns += banana_arc(68, 80, 11, step=2)              # high route over log 3
    spawns += banana_arc(81, 94, GROUND - 1, step=3)
    spawns += banana_arc(95, 106, GROUND, step=2)         # inside log 4
    spawns += banana_arc(122, 134, GROUND - 1, step=2)

    spawns += [
        Spawn("letter", 56, 12, {"letter": "A1"}),
        Spawn("letter", 45, GROUND, {"letter": "A2"}),    # deep in log 2
        Spawn("letter", 77, 12, {"letter": "P"}),         # on top of log 3
        Spawn("letter", 118, 11, {"letter": "E"}),
    ]
    spawns.append(Spawn("goal_totem", 134, GROUND))

    return LevelSpec(
        level_id="1-3",
        name="Hollow Log Run",
        cols=COLS,
        rows=ROWS,
        music_key="tangle_jungle",
        ground_rows=(GROUND, GROUND + 1),
        pits=pits,
        platforms=platforms,
        spawns=spawns,
        out_path="tangle_jungle/1_3_hollow_log_run.tmx",
        solids=solids,
    )


# ---------------------------------------------------------------------------
# Level 1-4, "The Saurian's Arena": King Saurus, World 1 boss.
#
# A short raised approach corridor (one Snapper, a checkpoint at the arena
# gate) leads onto the left safe ledge of a one-screen arena. The camera
# locks to the arena while Bongo is in it. Two-tile ledges at each end are
# the safe spots: King Saurus (56 px tall) charges, crashes into a ledge face
# and is dazed. Stomp him while he is dazed. Three stomps, each phase faster
# (phase 2+ adds a hop). After the second stomp he opens every cycle with a
# roar that drops coconuts; each shows a ground shadow before it falls.
# The goal totem only appears once he is beaten.
# ---------------------------------------------------------------------------

ARENA_COL = 14        # first column of the arena (the corridor is cols 1-13)
ARENA_COLS = 30       # exactly one screen wide


def spec_1_4() -> LevelSpec:
    A = ARENA_COL
    COLS, ROWS = A + ARENA_COLS, 18
    GROUND = 16
    LEDGE = 14            # corridor and left ledge surface row
    STUMP = A - 3
    spawns: list[Spawn] = [Spawn("spawn", 2, LEDGE)]

    solids = (
        (0, 0, 1, ROWS),              # left world wall
        (1, LEDGE, A + 3, 4),         # corridor floor, running onto the left safe ledge
        (STUMP, LEDGE - 1, 1, 1),     # stump: keeps the corridor Snapper off the ledge
        (COLS - 1, 0, 1, ROWS),       # right arena wall
        (COLS - 4, LEDGE, 3, 2),      # right safe ledge
    )

    # Approach corridor
    spawns += banana_arc(4, STUMP, LEDGE - 1)
    spawns.append(Spawn("banana", STUMP + 0.5, LEDGE - 2))  # on the stump
    spawns.append(Spawn("snapper", 8, LEDGE))
    spawns.append(Spawn("checkpoint", A - 2, LEDGE))   # arena gate

    spawns.append(Spawn("king_saurus", A + 18, GROUND, {
        "arena_left": str(A * TS), "arena_right": str(COLS * TS),
    }))
    spawns += [Spawn("banana", c + 0.5, 13) for c in (A + 1, A + 2, A + 3, COLS - 4, COLS - 3, COLS - 2)]
    spawns.append(Spawn("goal_totem", A + ARENA_COLS // 2 - 1, GROUND, {"requires_boss": "true"}))

    return LevelSpec(
        level_id="1-4",
        name="The Saurian's Arena",
        cols=COLS,
        rows=ROWS,
        music_key="king_saurus",
        ground_rows=(GROUND, GROUND + 1),
        pits=(),
        platforms=(),
        spawns=spawns,
        out_path="tangle_jungle/1_4_saurian_arena.tmx",
        solids=solids,
    )


ALL_SPECS = (spec_1_1, spec_1_2, spec_1_3, spec_1_4)


def main() -> int:
    ensure_placeholder_tileset()
    for spec_fn in ALL_SPECS:
        spec = spec_fn()
        out = LEVELS_DIR / spec.out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_tmx(spec), encoding="utf-8")
        n_obj = len(spec.spawns)
        print(f"Wrote {out.relative_to(ROOT)}  ({spec.cols}x{spec.rows}, {n_obj} objects)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
