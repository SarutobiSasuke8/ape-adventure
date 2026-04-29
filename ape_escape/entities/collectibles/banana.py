"""Banana — +1 collect count, 100 = extra life."""
from __future__ import annotations

import math

import pygame

from ape_escape.entities.entity import Entity
from ape_escape.render import palette as P

VALUE = 1


class Banana(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=14, h=18)
        self.bob_t = 0.0
        self.collected = False

    def update(self, dt: float, world) -> None:
        self.bob_t += dt

    def draw(self, surf: pygame.Surface, camera) -> None:
        if self.collected:
            return
        sp = camera.world_to_screen(self.pos)
        sx = int(sp.x)
        sy = int(sp.y) + int(math.sin(self.bob_t * 3.0) * 3)

        # Crescent banana shape using a polygon
        pts = [
            (sx + 7,  sy),
            (sx + 12, sy + 4),
            (sx + 13, sy + 10),
            (sx + 10, sy + 16),
            (sx + 6,  sy + 18),
            (sx + 3,  sy + 14),
            (sx + 4,  sy + 8),
            (sx + 7,  sy + 3),
        ]
        pygame.draw.polygon(surf, P.BANANA_YELLOW, pts)
        pygame.draw.polygon(surf, (200, 160, 20), pts, 1)

        # Tip dots
        pygame.draw.circle(surf, (180, 130, 10), (sx + 7, sy + 1), 2)
        pygame.draw.circle(surf, (180, 130, 10), (sx + 6, sy + 17), 2)
