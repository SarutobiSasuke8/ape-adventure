"""Bongo — the player. Phase 1.2 implementation target."""
from __future__ import annotations

import pygame

from ape_adventure.core import constants as C
from ape_adventure.core.input import InputSnapshot
from ape_adventure.entities.entity import Entity


class Player(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=28, h=44)
        self.health = C.PLAYER_MAX_HEALTH
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.invuln_timer = 0.0
        self.rolling_timer = 0.0
        self.state = "idle"  # idle | walk | run | jump | fall | roll | hurt | cheer

    def handle(self, snapshot: InputSnapshot) -> None:
        # TODO: write into intent vars consumed by update().
        ...

    def update(self, dt: float, world) -> None:
        # TODO: locomotion, gravity, jump w/ coyote+buffer, roll, i-frames.
        ...

    def draw(self, surf: pygame.Surface, camera) -> None:
        # TODO: blit current animation frame at camera.world_to_screen(self.rect.topleft).
        ...
