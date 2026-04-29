"""Multi-layer scrolling background."""
from __future__ import annotations

import pygame


class ParallaxLayer:
    def __init__(self, surface: pygame.Surface, scroll_factor: float) -> None:
        self.surface = surface
        self.scroll_factor = scroll_factor  # 0.0 = stuck to camera, 1.0 = world-locked

    def draw(self, target: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        # TODO: tile the surface horizontally, scroll by camera * scroll_factor.
        ...
