"""Banana bunch — +10 bananas or +1 health if hurt. Rare."""
from ape_adventure.entities.entity import Entity


class BananaBunch(Entity):
    BANANA_VALUE = 10

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=24, h=20)
