"""Slinger — stationary, throws coconuts in arc."""
from ape_escape.entities.enemies.enemy import Enemy


class Slinger(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=34, h=40, hp=1)
        self.throw_cooldown = 2.0
        self.cooldown_timer = 0.0
