"""In-level HUD: hearts, banana count, AAPE letters, pause hint."""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.render import palette as P


class Hud:
    def __init__(self) -> None:
        self.bananas = 0
        self.letters_collected: set[str] = set()
        self.health = C.PLAYER_MAX_HEALTH
        self._font = pygame.font.SysFont("arial", 20, bold=True)
        self._small = pygame.font.SysFont("arial", 15)
        self._t = 0.0

    def update(self, dt: float, bananas: int, letters: set[str], health: int) -> None:
        self.bananas = bananas
        self.letters_collected = letters
        self.health = health
        self._t += dt

    def draw(self, surf: pygame.Surface) -> None:
        w = C.SCREEN_WIDTH

        # --- Hearts (top-left) ---
        for i in range(C.PLAYER_MAX_HEALTH):
            filled = i < self.health
            col = P.HEART_FULL if filled else P.HEART_EMPTY
            cx, cy = 18 + i * 30, 20
            pygame.draw.circle(surf, col, (cx - 5, cy - 3), 7)
            pygame.draw.circle(surf, col, (cx + 5, cy - 3), 7)
            pts = [(cx - 11, cy - 1), (cx, cy + 10), (cx + 11, cy - 1)]
            pygame.draw.polygon(surf, col, pts)

        # --- Bananas (top-left, below hearts) ---
        bana_txt = self._font.render(f"x{self.bananas}", True, P.BANANA_YELLOW)
        # Small banana icon
        bx, by = 14, 44
        pts = [(bx+5,by),(bx+9,by+3),(bx+9,by+8),(bx+7,by+12),(bx+4,by+13),(bx+2,by+10),(bx+3,by+5)]
        pygame.draw.polygon(surf, P.BANANA_YELLOW, pts)
        surf.blit(bana_txt, (bx + 14, by - 2))

        # --- AAPE letters (top-center) ---
        letters_order = ("A1", "A2", "P", "E")
        display_chars = ("A", "A", "P", "E")
        total_w = len(letters_order) * 32
        lx = w // 2 - total_w // 2
        for key, char in zip(letters_order, display_chars):
            collected = key in self.letters_collected
            bg_col = P.LETTER_GOLD if collected else (50, 40, 20)
            txt_col = (40, 20, 8) if collected else (100, 80, 40)
            # Diamond
            cx_, cy_ = lx + 12, 20
            pulse = int(4 * math.sin(self._t * 3 + lx)) if collected else 0
            pts = [(cx_, cy_ - 12 - pulse), (cx_ + 12 + pulse, cy_),
                   (cx_, cy_ + 12 + pulse), (cx_ - 12 - pulse, cy_)]
            pygame.draw.polygon(surf, bg_col, pts)
            pygame.draw.polygon(surf, (200, 160, 40) if collected else (70, 55, 25), pts, 1)
            lbl = self._small.render(char, True, txt_col)
            surf.blit(lbl, lbl.get_rect(center=(cx_, cy_)))
            lx += 32

        # --- Pause hint (bottom-right, fades after 5s) ---
        hint = self._small.render("P — pause  |  Esc — title", True, (150, 190, 130))
        surf.blit(hint, (w - hint.get_width() - 8, C.SCREEN_HEIGHT - 24))
