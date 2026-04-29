"""In-level HUD: bananas, AAPE letters, hearts, pause hint."""
from __future__ import annotations

import pygame


class Hud:
    def __init__(self) -> None:
        self.bananas = 0
        self.letters_collected: set[str] = set()
        self.health = 2

    def draw(self, surf: pygame.Surface) -> None:
        # TODO: top-left bananas, top-center AAPE, top-right hearts, bottom-right pause hint (fading).
        ...
