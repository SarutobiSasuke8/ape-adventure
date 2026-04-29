"""Top-level Game class. Owns the window, the clock, and the active state."""
from __future__ import annotations

import sys
import pygame

from ape_adventure.core import constants as C
from ape_adventure.core.input import Input
from ape_adventure.core.states import TitleState, State
from ape_adventure.data.save import SaveData


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(C.WINDOW_TITLE)
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
