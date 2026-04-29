"""Smooth-follow camera with look-ahead. To be implemented in Phase 1.2."""
from __future__ import annotations

import pygame

from ape_adventure.core import constants as C


class Camera:
    def __init__(self, world_bounds: pygame.Rect) -> None:
        self.world_bounds = world_bounds
        self.offset = pygame.Vector2(0, 0)

    def follow(self, target_world_pos: pygame.Vector2, dt: float, facing: int) -> None:
        # TODO: lerp toward target with CAMERA_LOOKAHEAD bias in facing direction.
        ...

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        return world_pos - self.offset
