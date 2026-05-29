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


ALL_SPECS = (spec_1_1,)


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
