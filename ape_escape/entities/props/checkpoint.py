"""Checkpoint post. Touch it and a later death respawns Bongo here.

Health and hit rules are unchanged: a respawn still refills health, it only
moves where Bongo comes back. The most recently touched checkpoint wins.

Visuals are PLACEHOLDER procedural art (see docs/placeholder-art.md): a
wooden post with a cloth banner that is grey and furled until touched, then
raised and gold.
"""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.entities.entity import Entity
from ape_escape.render import palette as P

_RAISE_TIME = 0.35  # banner run-up after activation


class Checkpoint(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=24, h=64)
        self.active = False
        self.t = 0.0
        self._raise = 0.0  # 0 = furled at the bottom, 1 = raised to the top

    def activate(self) -> bool:
        """Mark this checkpoint as reached. Returns True the first time only."""
        if self.active:
            return False
        self.active = True
        return True

    def respawn_point(self) -> pygame.Vector2:
        """Player top-left for a respawn here (standing, centred on the post)."""
        return pygame.Vector2(self.rect.centerx - 14, self.rect.bottom - C.PLAYER_STAND_HEIGHT)

    def update(self, dt: float, world) -> None:
        self.t += dt
        if self.active and self._raise < 1.0:
            self._raise = min(1.0, self._raise + dt / _RAISE_TIME)

    def draw(self, surf: pygame.Surface, camera) -> None:
        sp = camera.world_to_screen(self.pos)
        sx, sy = int(sp.x), int(sp.y)
        H = self.rect.height
        pole_x = sx + 4

        # Base stone and post
        pygame.draw.ellipse(surf, (70, 60, 50), pygame.Rect(sx - 2, sy + H - 8, 28, 10))
        pygame.draw.rect(surf, P.WOOD_BARK, pygame.Rect(pole_x, sy + 4, 5, H - 6))
        pygame.draw.circle(surf, P.CANOPY_GOLD if self.active else P.WOOD_LIGHT, (pole_x + 2, sy + 4), 4)

        # Banner: hangs low and grey until reached, then raised in gold.
        top = sy + 8 + int((1.0 - self._raise) * 30) if self.active else sy + 38
        wave = int(math.sin(self.t * 5.0) * 2) if self.active else 0
        col = P.CANOPY_GOLD if self.active else (120, 115, 100)
        flag = [(pole_x + 5, top), (pole_x + 22, top + 5 + wave), (pole_x + 5, top + 12)]
        pygame.draw.polygon(surf, col, flag)
        pygame.draw.polygon(surf, P.WOOD_BARK, flag, 1)
