"""Base class for Saurian enemies."""
from __future__ import annotations

from ape_escape.entities.entity import Entity


class Enemy(Entity):
    def __init__(self, x: float, y: float, w: int, h: int, hp: int = 1) -> None:
        super().__init__(x, y, w, h)
        self.hp = hp
        self.armored = False  # Spike-Back overrides

    def take_hit(self, source: str) -> None:
        # source: "roll" | "ground_pound" | "thrown_item"
        if self.armored and source == "roll":
            return
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
