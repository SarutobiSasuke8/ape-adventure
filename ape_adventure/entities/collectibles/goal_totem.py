"""Goal totem — touching it ends the level."""
from ape_adventure.entities.entity import Entity


class GoalTotem(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=48, h=80)
        self.touched = False
