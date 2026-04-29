"""Frame orchestrator. Builds a frame from layered passes: BG → tiles → entities → FX → HUD."""
from __future__ import annotations

import pygame


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw_frame(self, level, camera, hud, particles) -> None:
        # TODO: blit parallax, then tilemap surface, then sorted entities, then particles, then HUD.
        ...
