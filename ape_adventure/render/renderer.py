"""Frame orchestrator: BG → tiles → entities → FX → HUD."""
from __future__ import annotations

import pygame

from ape_adventure.core import constants as C
from ape_adventure.render import palette as P


def draw_background(surf: pygame.Surface, camera_offset_x: float) -> None:
    """Simple jungle parallax gradient + distant canopy silhouette."""
    w, h = surf.get_size()

    # Sky gradient (top = deep blue-green, bottom = jungle mid)
    for y in range(h):
        t = y / h
        r = int(P.JUNGLE_DEEP[0] * (1 - t) + 10 * t)
        g = int(P.JUNGLE_DEEP[1] * (1 - t) + 40 * t)
        b = int(P.JUNGLE_DEEP[2] * (1 - t) + 22 * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    # Far background hills (parallax 0.15x)
    ox = int(camera_offset_x * 0.15) % w
    hill_color = (28, 72, 42)
    points = []
    step = 80
    for x in range(-ox - step, w + step, step):
        import math
        py = int(h * 0.55 + math.sin(x * 0.013) * 55)
        points.append((x, py))
    points.append((w, h))
    points.append((0, h))
    if len(points) >= 3:
        pygame.draw.polygon(surf, hill_color, points)

    # Mid canopy (parallax 0.30x)
    ox2 = int(camera_offset_x * 0.30) % (w + 200)
    canopy_color = (36, 95, 50)
    points2 = []
    step2 = 60
    for x in range(-ox2 - step2, w + step2, step2):
        import math
        py2 = int(h * 0.68 + math.sin(x * 0.022 + 1.2) * 38)
        points2.append((x, py2))
    points2.append((w, h))
    points2.append((0, h))
    if len(points2) >= 3:
        pygame.draw.polygon(surf, canopy_color, points2)


def draw_tiles(surf: pygame.Surface, level, camera) -> None:
    """Draw only tiles visible in the camera viewport."""
    tg = level.tile_grid
    if tg is None:
        return

    ts = tg.tile_size
    cx, cy = int(camera.offset.x), int(camera.offset.y)

    col_start = max(0, cx // ts)
    col_end = min(tg.width, (cx + C.SCREEN_WIDTH) // ts + 2)
    row_start = max(0, cy // ts)
    row_end = min(tg.height, (cy + C.SCREEN_HEIGHT) // ts + 2)

    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            if tg.data[row][col] == 0:
                continue
            sx = col * ts - cx
            sy = row * ts - cy
            tile_rect = pygame.Rect(sx, sy, ts, ts)

            # Base tile colour
            pygame.draw.rect(surf, P.JUNGLE_MID, tile_rect)

            # Dirt texture lines
            pygame.draw.line(surf, P.JUNGLE_DEEP,
                             (sx + 4, sy + ts // 2), (sx + ts - 4, sy + ts // 2))

            # Top surface: grass strip
            if tg.is_surface_tile(col, row):
                pygame.draw.rect(surf, P.JUNGLE_LIGHT, pygame.Rect(sx, sy, ts, 6))
                # Little grass tufts
                for gx in range(sx + 6, sx + ts - 2, 8):
                    pygame.draw.line(surf, P.LEAF_TINT, (gx, sy), (gx - 2, sy - 5))
                    pygame.draw.line(surf, P.LEAF_TINT, (gx, sy), (gx + 2, sy - 4))

            # Tile border (subtle)
            pygame.draw.rect(surf, P.JUNGLE_DEEP, tile_rect, 1)


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._work: pygame.Surface = pygame.Surface(screen.get_size())

    def draw_frame(
        self,
        level,
        camera,
        entities: list,
        particles=None,
        shake: tuple[int, int] = (0, 0),
    ) -> None:
        """Render one frame.  *shake* is a (dx, dy) pixel offset applied as
        a camera jitter — the world is drawn to an off-screen surface and
        blitted to the real screen with the offset so edges never show raw
        background colour."""
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
