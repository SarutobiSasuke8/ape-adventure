"""Generic particle pool. Used for dust, leaf, sparkle, splash, hit FX."""
from __future__ import annotations

import pygame


class ParticleSystem:
    def __init__(self, capacity: int = 256) -> None:
        self.capacity = capacity
        self.particles: list = []

    def emit(self, kind: str, x: float, y: float, count: int = 1) -> None:
        # TODO: spawn `count` particles of `kind` at (x, y).
        ...

    def update(self, dt: float) -> None:
        ...

    def draw(self, surf: pygame.Surface, camera) -> None:
        ...
