"""Axis-separated AABB collision against the tile grid. Phase 1.2."""
from __future__ import annotations

import pygame


def move_and_collide(rect: pygame.Rect, velocity: pygame.Vector2, tile_grid, dt: float):
    """Move rect by velocity * dt, resolving collisions axis-by-axis.

    Returns: (new_rect, new_velocity, collisions_dict).
    collisions_dict has bool flags: {'top', 'bottom', 'left', 'right'}.
    """
    # TODO: implement axis-separated sweep against tile_grid.solid_tiles_in(rect).
    raise NotImplementedError
