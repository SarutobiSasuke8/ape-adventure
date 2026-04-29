"""Level — owns tile grid, entities, parallax background, music key, world bounds."""
from __future__ import annotations

import pygame

from ape_escape.core.physics import TileGrid, SOLID


class Level:
    def __init__(self, level_id: str) -> None:
        self.level_id = level_id
        self.bounds = pygame.Rect(0, 0, 1, 1)
        self.tile_grid: TileGrid | None = None
        self.entities: list = []
        self.music_key: str = ""
        self.spawn_point = pygame.Vector2(0, 0)
        self.total_bananas = 0
        self.total_letters = 0


def build_test_level() -> Level:
    """Hardcoded playground: ground floor, platforms, pits, enemies, collectibles."""
    from ape_escape.entities.enemies.snapper import Snapper
    from ape_escape.entities.enemies.hopper import Hopper
    from ape_escape.entities.collectibles.banana import Banana
    from ape_escape.entities.collectibles.aape_letter import AapeLetter, LETTERS
    from ape_escape.entities.collectibles.goal_totem import GoalTotem

    TS = 32
    COLS = 125   # 4000 px wide
    ROWS = 18    # 576 px tall

    lvl = Level("test_playground")
    lvl.bounds = pygame.Rect(0, 0, COLS * TS, ROWS * TS)
    lvl.music_key = "tangle_jungle"

    g = TileGrid(COLS, ROWS, TS)

    # Ground floor (rows 16-17) with pits
    PIT_RANGES = [(20, 23), (55, 58), (90, 93)]
    for col in range(COLS):
        in_pit = any(lo <= col <= hi for lo, hi in PIT_RANGES)
        if not in_pit:
            g.set(col, 16, SOLID)
            g.set(col, 17, SOLID)

    # Floating platforms: (row, col_start, col_end_exclusive)
    PLATFORMS = [
        (13,  4, 11),   # near start
        (11, 14, 21),   # bridge over pit 1
        (13, 26, 33),
        (10, 37, 43),
        (12, 47, 54),   # bridge over pit 2
        ( 9, 60, 66),
        (12, 70, 76),
        (14, 80, 86),
        (11, 87, 94),   # bridge over pit 3
        ( 9, 97, 103),
        (13, 107, 113),
        (11, 115, 121),
    ]
    for row, c0, c1 in PLATFORMS:
        for col in range(c0, c1):
            g.set(col, row, SOLID)

    lvl.tile_grid = g
    lvl.spawn_point = pygame.Vector2(2 * TS, 16 * TS - 48)

    entities: list = []

    # Helper: entity stands on top of a platform/ground row
    def on_plat(col: float, row: int, ent_h: int) -> tuple[float, float]:
        return col * TS, row * TS - ent_h

    # --- Snappers ---
    snappers = [
        (8 * TS,        16 * TS - 28),   # ground floor, easy intro
        (17 * TS,       11 * TS - 28),   # platform B
        (29 * TS,       13 * TS - 28),   # platform C
        (40 * TS,       10 * TS - 28),   # platform D
        (72 * TS,       12 * TS - 28),   # platform G
        (99 * TS,        9 * TS - 28),   # platform J
    ]
    for sx, sy in snappers:
        entities.append(Snapper(sx, sy))

    # --- Bananas ---
    # Ground leading sections + platform arcs
    banana_positions = [
        # Section 1: ground toward first gap
        *[(x * TS + 8, 16 * TS - 24) for x in range(4, 19, 2)],
        # Platform A
        *[(x * TS + 8, 13 * TS - 24) for x in range(5, 10, 2)],
        # Platform B bridge
        *[(x * TS + 8, 11 * TS - 24) for x in range(15, 20, 2)],
        # Ground section 2
        *[(x * TS + 8, 16 * TS - 24) for x in range(24, 45, 3)],
        # Platform D high
        *[(x * TS + 8, 10 * TS - 24) for x in range(38, 43, 2)],
        # Platform F highest
        *[(x * TS + 8, 9 * TS - 24)  for x in range(61, 65)],
        # Ground section 3
        *[(x * TS + 8, 16 * TS - 24) for x in range(60, 90, 3)],
        # Platform J
        *[(x * TS + 8, 9 * TS - 24)  for x in range(98, 102)],
        # Final stretch
        *[(x * TS + 8, 16 * TS - 24) for x in range(94, 123, 2)],
    ]
    bananas = [Banana(bx, by) for bx, by in banana_positions]
    entities.extend(bananas)
    lvl.total_bananas = len(bananas)

    # --- AAPE Letters (4, one per world — placed on tricky spots) ---
    aape_positions = [
        ("A1", 9  * TS, 13 * TS - 40),   # platform A, after snapper
        ("A2", 40 * TS, 10 * TS - 40),   # platform D high
        ("P",  62 * TS,  9 * TS - 40),   # platform F, highest point
        ("E",  100 * TS, 9 * TS - 40),   # platform J, near end
    ]
    for letter, lx, ly in aape_positions:
        entities.append(AapeLetter(lx, ly, letter))
    lvl.total_letters = len(aape_positions)

    # --- Hoppers (introduced mid-level, harder to read than Snappers) ---
    hopper_positions = [
        (32 * TS,  16 * TS - 24),   # ground floor, section 2 — first encounter
        (51 * TS,  12 * TS - 24),   # platform E (bridge over pit 2)
        (63 * TS,   9 * TS - 24),   # platform F, highest point — tricky
        (109 * TS, 13 * TS - 24),   # platform K, near the end
    ]
    for hx, hy in hopper_positions:
        entities.append(Hopper(hx, hy))

    # --- Goal totem (end of level) ---
    totem_x = 119 * TS
    totem_y = 16 * TS - 80
    entities.append(GoalTotem(totem_x, totem_y))

    lvl.entities = entities
    return lvl
