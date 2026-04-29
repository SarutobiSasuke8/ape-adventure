"""State machine. Each state implements enter/handle/update/draw/exit."""
from __future__ import annotations

import pygame

from ape_adventure.core import constants as C
from ape_adventure.core.input import InputSnapshot


class State:
    def __init__(self, game) -> None:
        self.game = game

    def enter(self) -> None: ...
    def exit(self) -> None: ...
    def handle(self, snapshot: InputSnapshot) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surf: pygame.Surface) -> None: ...


class TitleState(State):
    """Placeholder title screen. Replace with painted art later."""

    def __init__(self, game) -> None:
        super().__init__(game)
        self.font_big = pygame.font.SysFont("arial", 64, bold=True)
        self.font_small = pygame.font.SysFont("arial", 22)
        self.t = 0.0

    def handle(self, snapshot: InputSnapshot) -> None:
        if snapshot.confirm or snapshot.start:
            # Placeholder — wire up world map state when it exists.
            pass
        if snapshot.quit:
            self.game.running = False

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((28, 60, 38))  # jungle deep green placeholder
        title = self.font_big.render("APE ADVENTURE", True, (250, 210, 90))
        sub = self.font_small.render("vertical slice — scaffold", True, (200, 230, 200))
        rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 20))
        surf.blit(title, rect)
        surf.blit(sub, sub.get_rect(center=(C.SCREEN_WIDTH // 2, rect.bottom + 20)))


class WorldMapState(State):
    """World node map. To be implemented in Phase 1.3."""


class LevelState(State):
    """In-level gameplay. To be implemented in Phase 1.2."""


class PauseState(State):
    """Paused overlay on top of LevelState. To be implemented in Phase 1.1."""


class ResultsState(State):
    """End-of-level summary. To be implemented in Phase 1.3."""
