"""AAPE letter — collect all four (A, A, P, E) per level for an extra life and bonus reveal."""
from ape_adventure.entities.entity import Entity


class AapeLetter(Entity):
    LETTERS = ("A1", "A2", "P", "E")

    def __init__(self, x: float, y: float, letter: str) -> None:
        assert letter in self.LETTERS
        super().__init__(x, y, w=24, h=28)
        self.letter = letter
