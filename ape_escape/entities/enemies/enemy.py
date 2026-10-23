"""Base class for Saurian enemies."""
from __future__ import annotations

from ape_escape.entities.entity import Entity


class Enemy(Entity):
    """Shared enemy contract used by LevelState's contact checks.

    Ordinary enemies die to one stomp or one roll. Tougher enemies (the boss)
    override ``on_stomp`` / ``on_roll`` / ``harmful`` to gate when they can be
    damaged and when touching them is safe.
    """

    STOMP_BOUNCE = -380.0  # player's upward velocity after stomping this enemy

    def __init__(self, x: float, y: float, w: int, h: int, hp: int = 1) -> None:
        super().__init__(x, y, w, h)
        self.hp = hp
        self.armored = False  # Spike-Back overrides
        self._dying = False

    @property
    def harmful(self) -> bool:
        """True if side contact hurts the player right now."""
        return not self._dying

    def on_stomp(self) -> bool:
        """Player landed on top. Returns True if the stomp damaged the enemy."""
        self.die()
        return True

    def on_roll(self) -> bool:
        """Player rolled into it. Returns True if the roll damaged the enemy."""
        if self.armored:
            return False
        self.die()
        return True

    def die(self) -> None:
        self._dying = True
        self.alive = False

    def take_hit(self, source: str) -> None:
        # source: "roll" | "ground_pound" | "thrown_item"
        if self.armored and source == "roll":
            return
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
