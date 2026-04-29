"""Base Entity. Everything drawable in a level inherits from this."""
from __future__ import annotations

import pygame


class Entity:
    def __init__(self, x: float, y: float, w: int, h: int) -> None:
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.facing = 1  # +1 right, -1 left
        self.alive = True

    def update(self, dt: float, world) -> None: ...

    def draw(self, surf: pygame.Surface, camera) -> None: ...
