"""Bonus barrel — entering it warps the player into a small skill challenge sub-room."""
from ape_adventure.entities.entity import Entity


class BonusBarrel(Entity):
    def __init__(self, x: float, y: float, sub_level_id: str) -> None:
        super().__init__(x, y, w=32, h=40)
        self.sub_level_id = sub_level_id
        self.entered = False
