"""Goal totem — touch it to complete the level."""
from __future__ import annotations

import math

import pygame

from ape_adventure.entities.entity import Entity
from ape_adventure.render import palette as P


class GoalTotem(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=48, h=80)
        self.t = 0.0
        self.touched = False

    def update(self, dt: float, world) -> None:
        self.t += dt

    def draw(self, surf: pygame.Surface, camera) -> None:
        sp = camera.world_to_screen(self.pos)
        sx, sy = int(sp.x), int(sp.y)
        cx = sx + 24

        pulse = 0.5 + 0.5 * math.sin(self.t * 2.8)

        # Pole
        pygame.draw.rect(surf, P.WOOD_BARK,  pygame.Rect(cx - 8,  sy + 28, 16, 52))
        pygame.draw.rect(surf, P.WOOD_LIGHT, pygame.Rect(cx - 4,  sy + 28, 6,  52))

        # Ornament circle glow
        glow_r = int(24 + pulse * 8)
        glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (250, 210, 90, int(90 * pulse)), (glow_r + 2, glow_r + 2), glow_r)
        surf.blit(glow, (cx - glow_r - 2, sy + 16 - glow_r - 2))

        # Ornament face
        pygame.draw.circle(surf, P.WOOD_BARK,  (cx, sy + 16), 20)
        pygame.draw.circle(surf, P.WOOD_LIGHT, (cx, sy + 16), 15)
        # Carved eyes
        pygame.draw.circle(surf, P.CANOPY_GOLD, (cx - 7, sy + 11), 5)
        pygame.draw.circle(surf, P.CANOPY_GOLD, (cx + 7, sy + 11), 5)
        pygame.draw.circle(surf, P.WOOD_BARK,  (cx - 7, sy + 11), 2)
        pygame.draw.circle(surf, P.WOOD_BARK,  (cx + 7, sy + 11), 2)
        # Carved mouth arc
        pygame.draw.arc(surf, P.CANOPY_GOLD,
                        pygame.Rect(cx - 8, sy + 16, 16, 10), math.pi, 2 * math.pi, 2)

        # "GOAL" label above
        if not hasattr(self, "_font"):
            self._font = pygame.font.SysFont("arial", 13, bold=True)
        lbl = self._font.render("GOAL", True, P.CANOPY_GOLD)
        surf.blit(lbl, lbl.get_rect(center=(cx, sy - 6)))
