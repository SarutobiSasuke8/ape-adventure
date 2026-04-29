"""Snapper — walks back and forth on a platform. World 1 staple."""
from ape_adventure.entities.enemies.enemy import Enemy


class Snapper(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=32, h=28, hp=1)
        self.patrol_speed = 60.0
