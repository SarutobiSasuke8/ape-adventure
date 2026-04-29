"""Screen wipes and fades between states."""
from __future__ import annotations

import pygame


def fade_out(surf: pygame.Surface, t: float, duration: float = 0.5) -> None:
    """Draw a black overlay alpha-ramping from 0 to 255 over `duration` seconds."""
    alpha = max(0, min(255, int(255 * (t / duration))))
    overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surf.blit(overlay, (0, 0))
