"""AAPE letters — collect all four in a level for an extra life."""
from __future__ import annotations

import math

import pygame

from ape_adventure.entities.entity import Entity
from ape_adventure.render import palette as P

LETTERS = ("A1", "A2", "P", "E")
_font_cache: pygame.font.Font | None = None


def _font() -> pygame.font.Font:
    global _font_cache
    if _font_cache is None:
        _font_cache = pygame.font.SysFont("arial", 15, bold=True)
    return _font_cache


class AapeLetter(Entity):
    def __init__(self, x: float, y: float, letter: str) -> None:
        assert letter in LETTERS
        super().__init__(x, y, w=26, h=26)
        self.letter = letter
        self.float_t = 0.0
        self.collected = False

    def update(self, dt: float, world) -> None:
        self.float_t += dt

    def draw(self, surf: pygame.Surface, camera) -> None:
        if self.collected:
            return
        sp = camera.world_to_screen(self.pos)
        sx = int(sp.x)
        sy = int(sp.y) + int(math.sin(self.float_t * 2.2) * 4)
        cx, cy = sx + 13, sy + 13

        # Outer glow
        glow = pygame.Surface((52, 52), pygame.SRCALPHA)
        alpha = int(80 + 40 * math.sin(self.float_t * 3.0))
        pygame.draw.circle(glow, (*P.LETTER_GOLD, alpha), (26, 26), 22)
        surf.blit(glow, (cx - 26, cy - 26))

        # Diamond body
        pts = [(cx, sy), (sx + 26, cy), (cx, sy + 26), (sx, cy)]
        pygame.draw.polygon(surf, P.LETTER_GOLD, pts)
        pygame.draw.polygon(surf, (255, 235, 120), pts, 2)

        # Letter (A1/A2 → "A")
        char = self.letter[0]
        txt = _font().render(char, True, (50, 25, 8))
        surf.blit(txt, txt.get_rect(center=(cx, cy)))
