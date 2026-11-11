"""Smooth-follow camera with look-ahead and world-bound clamping."""
from __future__ import annotations

import pygame

from ape_escape.core import constants as C


class Camera:
    def __init__(self, world_bounds: pygame.Rect) -> None:
        self.world_bounds = world_bounds
        self.offset = pygame.Vector2(0, 0)
        self._target_offset = pygame.Vector2(0, 0)
        # Optional arena lock: while the target is inside this rect, the view
        # stays inside it too (boss arenas exactly one screen wide).
        self.lock_rect: pygame.Rect | None = None

    def _clamp_x(self, x: float, target: pygame.Vector2) -> float:
        max_x = max(0, self.world_bounds.width - C.SCREEN_WIDTH)
        x = max(0.0, min(float(max_x), x))
        lock = self.lock_rect
        if lock is not None and lock.left <= target.x <= lock.right:
            hi = max(lock.left, lock.right - C.SCREEN_WIDTH)
            x = max(float(lock.left), min(float(hi), x))
        return x

    def follow(self, target: pygame.Vector2, dt: float, facing: int) -> None:
        half_w = C.SCREEN_WIDTH * 0.5
        half_h = C.SCREEN_HEIGHT * 0.5

        ideal_x = target.x - half_w + facing * C.CAMERA_LOOKAHEAD
        ideal_y = target.y - half_h

        max_y = max(0, self.world_bounds.height - C.SCREEN_HEIGHT)
        ideal_x = self._clamp_x(ideal_x, target)
        ideal_y = max(0.0, min(float(max_y), ideal_y))

        t = min(1.0, C.CAMERA_LERP * dt)
        self.offset.x += (ideal_x - self.offset.x) * t
        self.offset.y += (ideal_y - self.offset.y) * t

    def snap_to(self, target: pygame.Vector2) -> None:
        half_w = C.SCREEN_WIDTH * 0.5
        half_h = C.SCREEN_HEIGHT * 0.5
        self.offset.x = self._clamp_x(target.x - half_w, target)
        self.offset.y = max(0.0, min(float(self.world_bounds.height - C.SCREEN_HEIGHT), target.y - half_h))

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        return world_pos - self.offset
