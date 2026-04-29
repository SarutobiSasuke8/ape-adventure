"""Banana — basic collectible, +1 to count, 100 = extra life."""
from ape_adventure.entities.entity import Entity


class Banana(Entity):
    VALUE = 1

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=16, h=16)
        self.bob_t = 0.0
