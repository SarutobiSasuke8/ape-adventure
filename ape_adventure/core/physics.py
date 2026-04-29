"""Axis-separated AABB collision against the tile grid."""
from __future__ import annotations

import pygame

SOLID = 1


class TileGrid:
    def __init__(self, width: int, height: int, tile_size: int) -> None:
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.data: list[list[int]] = [[0] * width for _ in range(height)]

    def get(self, col: int, row: int) -> int:
        if 0 <= col < self.width and 0 <= row < self.height:
            return self.data[row][col]
        return SOLID  # out of bounds = solid wall

    def set(self, col: int, row: int, tile_type: int) -> None:
        if 0 <= col < self.width and 0 <= row < self.height:
            self.data[row][col] = tile_type

    def fill_rect(self, col: int, row: int, cols: int, rows: int, tile_type: int) -> None:
        for r in range(row, row + rows):
            for c in range(col, col + cols):
                self.set(c, r, tile_type)

    def solid_tiles_near(self, rect: pygame.Rect) -> list[pygame.Rect]:
        ts = self.tile_size
        c0 = max(0, rect.left // ts)
        c1 = min(self.width - 1, (rect.right - 1) // ts)
        r0 = max(0, rect.top // ts)
        r1 = min(self.height - 1, (rect.bottom - 1) // ts)
        result = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if self.data[r][c] == SOLID:
                    result.append(pygame.Rect(c * ts, r * ts, ts, ts))
        return result

    def is_surface_tile(self, col: int, row: int) -> bool:
        """True if this tile is solid and the tile above it is empty."""
        return self.get(col, row) == SOLID and self.get(col, row - 1) != SOLID


def move_and_collide(
    pos: pygame.Vector2,
    rect: pygame.Rect,
    velocity: pygame.Vector2,
    tile_grid: TileGrid,
    dt: float,
) -> tuple[pygame.Vector2, pygame.Vector2, dict[str, bool]]:
    """Move pos by velocity*dt, resolve AABB collisions axis-by-axis.

    Returns (new_pos, new_velocity, collisions).
    """
    cols: dict[str, bool] = {"top": False, "bottom": False, "left": False, "right": False}

    # --- Horizontal ---
    new_x = pos.x + velocity.x * dt
    rect.x = int(new_x)
    for tile in tile_grid.solid_tiles_near(rect):
        if rect.colliderect(tile):
            if velocity.x > 0:
                rect.right = tile.left
                cols["right"] = True
            elif velocity.x < 0:
                rect.left = tile.right
                cols["left"] = True
    new_x = float(rect.x)

    # --- Vertical ---
    new_y = pos.y + velocity.y * dt
    rect.y = int(new_y)
    for tile in tile_grid.solid_tiles_near(rect):
        if rect.colliderect(tile):
            if velocity.y > 0:
                rect.bottom = tile.top
                cols["bottom"] = True
            elif velocity.y < 0:
                rect.top = tile.bottom
                cols["top"] = True
    new_y = float(rect.y)

    new_vel = pygame.Vector2(
        0.0 if (cols["left"] or cols["right"]) else velocity.x,
        0.0 if (cols["top"] or cols["bottom"]) else velocity.y,
    )

    return pygame.Vector2(new_x, new_y), new_vel, cols
