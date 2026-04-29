"""Hopper — small, fast, hops along the ground."""
from ape_adventure.entities.enemies.enemy import Enemy


class Hopper(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=26, h=24, hp=1)
        self.hop_impulse = -360.0
        self.hop_cooldown = 0.8
        self.cooldown_timer = 0.0
