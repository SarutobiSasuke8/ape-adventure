"""Frame orchestrator: BG → tiles → entities → FX → HUD."""
from __future__ import annotations

import math

import pygame

from ape_adventure.core import constants as C
from ape_adventure.render import palette as P


# ---------------------------------------------------------------------------
# Deterministic per-tile variation (no random() calls during draw)
# ---------------------------------------------------------------------------

def _tv(col: int, row: int) -> int:
    """Cheap position hash → 0-99.  Same value every frame for same tile."""
    return (col * 2654435761 ^ row * 2246822519) % 100


# ---------------------------------------------------------------------------
# Background layers
# ---------------------------------------------------------------------------

def draw_background(surf: pygame.Surface, camera_offset_x: float) -> None:
    """Three-layer parallax jungle background."""
    w, h = surf.get_size()

    # Sky gradient — deep teal-green top, warmer mid-green bottom
    for y in range(h):
        t = y / h
        r = int(18 * (1 - t) + 28 * t)
        g = int(58 * (1 - t) + 72 * t)
        b = int(38 * (1 - t) + 32 * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    # --- Layer 1: distant misty hills (0.12x) ---
    ox1 = int(camera_offset_x * 0.12) % (w + 160)
    hill_col = (22, 60, 38)
    pts = []
    for x in range(-ox1 - 80, w + 80, 70):
        py = int(h * 0.58 + math.sin(x * 0.011) * 50 + math.sin(x * 0.031) * 18)
        pts.append((x, py))
    pts += [(w, h), (0, h)]
    if len(pts) >= 3:
        pygame.draw.polygon(surf, hill_col, pts)

    # --- Layer 2: jungle tree silhouettes (0.28x) ---
    ox2 = int(camera_offset_x * 0.28) % (w + 300)
    tree_col  = (30, 80, 46)
    tree_col2 = (38, 95, 54)
    # Ground fill behind trees
    pygame.draw.rect(surf, tree_col, pygame.Rect(0, int(h * 0.62), w, h))
    # Individual trees: trunk + canopy blob
    tree_spacing = 110
    for tx in range(-ox2 - tree_spacing, w + tree_spacing, tree_spacing):
        v = _tv(tx // tree_spacing, 0)
        height_frac = 0.20 + (v % 25) * 0.006
        tree_h = int(h * height_frac)
        tree_top_y = int(h * 0.62) - tree_h
        trunk_w = 8 + v % 6
        # Canopy blob (ellipse)
        canopy_r = 28 + v % 22
        canopy_cx = tx + 20
        canopy_cy = tree_top_y + canopy_r // 2
        pygame.draw.ellipse(surf, tree_col2,
                            pygame.Rect(canopy_cx - canopy_r, canopy_cy - canopy_r,
                                        canopy_r * 2, int(canopy_r * 1.3)))
        # Secondary canopy lobe
        if v % 3 != 0:
            r2 = canopy_r - 8
            pygame.draw.ellipse(surf, tree_col,
                                pygame.Rect(canopy_cx + r2 // 2 - r2, canopy_cy - r2 + 5,
                                            r2 * 2, int(r2 * 1.2)))

    # --- Layer 3: near canopy fringe (0.42x) ---
    ox3 = int(camera_offset_x * 0.42) % (w + 200)
    canopy_col = (36, 98, 52)
    pts3 = []
    for x in range(-ox3 - 60, w + 60, 52):
        py = int(h * 0.72 + math.sin(x * 0.020 + 1.1) * 32 + math.sin(x * 0.044) * 14)
        pts3.append((x, py))
    pts3 += [(w, h), (0, h)]
    if len(pts3) >= 3:
        pygame.draw.polygon(surf, canopy_col, pts3)

    # Leaf cluster bumps along the canopy edge
    leaf_col = (50, 120, 62)
    for lx in range(-ox3 - 30, w + 30, 36):
        v = _tv(lx // 36, 3)
        lpy = int(h * 0.70 + math.sin(lx * 0.020 + 1.1) * 32)
        lr  = 14 + v % 12
        pygame.draw.circle(surf, leaf_col, (lx + 18, lpy - lr // 2), lr)


# ---------------------------------------------------------------------------
# Tile rendering
# ---------------------------------------------------------------------------

def draw_tiles(surf: pygame.Surface, level, camera) -> None:
    """Draw visible tiles with grass, depth shading, vines, and props."""
    tg = level.tile_grid
    if tg is None:
        return

    ts  = tg.tile_size
    cx  = int(camera.offset.x)
    cy  = int(camera.offset.y)

    col_start = max(0, cx // ts)
    col_end   = min(tg.width,  (cx + C.SCREEN_WIDTH)  // ts + 2)
    row_start = max(0, cy // ts)
    row_end   = min(tg.height, (cy + C.SCREEN_HEIGHT) // ts + 2)

    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            if tg.data[row][col] == 0:
                continue

            sx = col * ts - cx
            sy = row * ts - cy
            tr = pygame.Rect(sx, sy, ts, ts)
            v  = _tv(col, row)
            is_surface = tg.is_surface_tile(col, row)

            # --- Base tile colour (slightly darker the deeper the tile) ---
            depth = min(row / max(1, tg.height), 1.0)
            base_r = int(P.JUNGLE_MID[0] * (1 - depth * 0.22))
            base_g = int(P.JUNGLE_MID[1] * (1 - depth * 0.22))
            base_b = int(P.JUNGLE_MID[2] * (1 - depth * 0.22))
            pygame.draw.rect(surf, (base_r, base_g, base_b), tr)

            # Subtle dirt streaks
            streak_y = sy + ts // 2 + (v % 6) - 3
            pygame.draw.line(surf, P.JUNGLE_DEEP,
                             (sx + 5, streak_y), (sx + ts - 5, streak_y))
            if v % 3 == 0:
                pygame.draw.line(surf, P.JUNGLE_DEEP,
                                 (sx + 8, streak_y + 6), (sx + ts - 8, streak_y + 6))

            # Small rock speckle
            if v % 7 == 0:
                rx, ry = sx + 6 + v % 12, sy + ts - 10 - v % 8
                pygame.draw.ellipse(surf, P.JUNGLE_DEEP, pygame.Rect(rx, ry, 8, 5))

            # --- Left-edge shadow (gives tiles a stacked look) ---
            pygame.draw.rect(surf, (base_r - 12, base_g - 12, base_b - 12),
                             pygame.Rect(sx, sy, 3, ts))

            # --- Tile border ---
            pygame.draw.rect(surf, P.JUNGLE_DEEP, tr, 1)

            # --- Surface tile extras ---
            if is_surface:
                # Grass strip — two-tone
                grass_r = int(P.JUNGLE_LIGHT[0] * (0.85 + (v % 20) * 0.008))
                grass_g = int(P.JUNGLE_LIGHT[1] * (0.85 + (v % 20) * 0.008))
                grass_b = int(P.JUNGLE_LIGHT[2] * (0.85 + (v % 20) * 0.008))
                pygame.draw.rect(surf, (grass_r, grass_g, grass_b),
                                 pygame.Rect(sx, sy, ts, 5))
                pygame.draw.rect(surf, P.LEAF_TINT,
                                 pygame.Rect(sx + 1, sy, ts - 2, 2))

                # Grass tufts (deterministic spacing)
                tuft_offsets = [5, 12, 20, 28] if ts >= 32 else [6, 18]
                for gx_off in tuft_offsets:
                    gx   = sx + gx_off + (v % 4) - 2
                    h1   = 4 + (v % 3)
                    lean = (v % 5) - 2
                    pygame.draw.line(surf, P.LEAF_TINT,
                                     (gx, sy), (gx + lean, sy - h1))
                    pygame.draw.line(surf, P.LEAF_TINT,
                                     (gx, sy), (gx - lean - 1, sy - h1 + 1))

                # Occasional flower (15% of surface tiles)
                if v % 7 == 0:
                    fx, fy = sx + 14 + v % 8, sy - 7
                    petal_col = (220, 100, 150) if v % 2 == 0 else (255, 200, 60)
                    pygame.draw.circle(surf, petal_col, (fx, fy), 3)
                    pygame.draw.circle(surf, (255, 245, 200), (fx, fy), 1)

                # Hanging vine from platform undersides (tile above is empty)
                has_floor_below = tg.get(col, row + 1) != 0
                if not has_floor_below:
                    vine_len = 20 + (v % 4) * 14   # 20, 34, 48, or 62 px
                    vx_off   = 4 + v % (ts - 8)
                    vx_w     = sx + vx_off
                    vx_w2    = sx + vx_off + 10 + v % 8
                    _draw_vine(surf, vx_w,  sy + ts, vine_len, v)
                    if v % 3 != 0:
                        _draw_vine(surf, vx_w2, sy + ts, vine_len - 10, (v * 7) % 100)


def _draw_vine(surf: pygame.Surface, x: int, y: int, length: int, seed: int) -> None:
    """Draw a short wavy vine hanging downward from (x, y)."""
    seg = 8
    cx, cy = x, y
    for i in range(length // seg):
        t     = i / max(1, length // seg - 1)
        sway  = int(math.sin(i * 0.9 + seed * 0.1) * 3)
        nx    = cx + sway
        ny    = cy + seg
        col   = (50, 110, 40) if i % 2 == 0 else (40, 90, 30)
        pygame.draw.line(surf, col, (cx, cy), (nx, ny), 2)
        # Leaf nub every other segment
        if i % 2 == 0:
            leaf_col = (75, 145, 55)
            pygame.draw.ellipse(surf, leaf_col,
                                pygame.Rect(nx + 2, ny - 3, 7, 5))
        cx, cy = nx, ny


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._work  = pygame.Surface(screen.get_size())

    def draw_frame(
        self,
        level,
        camera,
        entities: list,
        particles=None,
        shake: tuple[int, int] = (0, 0),
    ) -> None:
        """Render one complete frame.

        *shake* is a (dx, dy) pixel jitter applied by blitting the rendered
        scene to the real screen at an offset — no edge bleed.
        """
        target = self._work if (shake[0] or shake[1]) else self.screen

        draw_background(target, camera.offset.x)
        draw_tiles(target, level, camera)

        for ent in entities:
            ent.draw(target, camera)

        if particles is not None:
            particles.draw(target, camera)

        if shake[0] or shake[1]:
            self.screen.fill((0, 0, 0))
            self.screen.blit(target, shake)
