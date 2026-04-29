"""Top-level Game class. Owns the window, the clock, and the active state."""
from __future__ import annotations

import sys
import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import Input
from ape_escape.core.states import TitleState, State
from ape_escape.data.save import SaveData


def _make_icon() -> pygame.Surface:
    """Draw a 32×32 ape-face icon procedurally."""
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)

    FUR        = (100, 58, 28)
    FUR_DARK   = (70,  38, 14)
    FACE_PATCH = (210, 170, 120)
    EYE        = (18,  10,  6)
    EYE_SHINE  = (255, 255, 255)
    NOSE       = (60,  28,  12)
    MOUTH      = (60,  28,  12)

    # Ears (behind head)
    pygame.draw.circle(surf, FUR_DARK, (5,  12), 5)
    pygame.draw.circle(surf, FUR_DARK, (27, 12), 5)
    pygame.draw.circle(surf, FACE_PATCH, (5,  12), 3)
    pygame.draw.circle(surf, FACE_PATCH, (27, 12), 3)

    # Head
    pygame.draw.circle(surf, FUR, (16, 15), 13)

    # Face patch (lighter muzzle area)
    pygame.draw.ellipse(surf, FACE_PATCH, pygame.Rect(8, 14, 16, 13))

    # Brow ridge (slightly darker strip)
    pygame.draw.ellipse(surf, FUR_DARK, pygame.Rect(6, 7, 20, 6))

    # Eyes
    pygame.draw.circle(surf, EYE,       (11, 12), 3)
    pygame.draw.circle(surf, EYE,       (21, 12), 3)
    pygame.draw.circle(surf, EYE_SHINE, (12, 11), 1)
    pygame.draw.circle(surf, EYE_SHINE, (22, 11), 1)

    # Nose
    pygame.draw.ellipse(surf, NOSE, pygame.Rect(12, 18, 8, 5))
    pygame.draw.circle(surf, FUR_DARK, (13, 20), 1)
    pygame.draw.circle(surf, FUR_DARK, (19, 20), 1)

    # Mouth — a small curved line
    pygame.draw.arc(surf, MOUTH, pygame.Rect(11, 21, 10, 5), 3.5, 5.9, 2)

    return surf


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(C.WINDOW_TITLE)
        pygame.display.set_icon(_make_icon())          # must come before set_mode
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.input = Input()
        self.save = SaveData()
        self.state: State = TitleState(self)
        self.next_state: State | None = None
        self.running = True

    def change_state(self, new_state: State) -> None:
        self.next_state = new_state

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(C.FPS) / 1000.0

            if self.next_state is not None:
                self.state.exit()
                self.state = self.next_state
                self.next_state = None
                self.state.enter()

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            snapshot = self.input.poll(events)
            self.state.handle(snapshot)
            self.state.update(dt)
            self.state.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)
