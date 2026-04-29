"""Headless smoke test for the Ape Adventure package."""
from __future__ import annotations

import os
import sys

os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot
from ape_escape.core.states import LevelState, ResultsState


class FakeGame:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        self.next_state = None
        self.running = True

    def change_state(self, new_state) -> None:
        self.next_state = new_state


def run_frames(state: LevelState, screen: pygame.Surface, snapshots: list[InputSnapshot]) -> None:
    for snap in snapshots:
        pygame.event.pump()
        state.handle(snap)
        state.update(1 / C.FPS)
        state.draw(screen)


def main() -> int:
    pygame.init()
    game = FakeGame()
    state = LevelState(game)
    state.enter()

    try:
        assert state.player is not None
        assert state.level is not None
        assert state.player.health == C.PLAYER_MAX_HEALTH

        opening_inputs = (
            [InputSnapshot(move_x=1.0, run=True) for _ in range(45)]
            + [InputSnapshot(move_x=1.0, jump=True, jump_held=True) for _ in range(8)]
            + [InputSnapshot(move_x=1.0, jump_held=True) for _ in range(42)]
            + [InputSnapshot(move_x=1.0) for _ in range(80)]
        )
        run_frames(state, game.screen, opening_inputs)

        state._trigger_death()
        assert state.player.dead
        assert state.player.health == 0
        run_frames(state, game.screen, [InputSnapshot() for _ in range(90)])
        assert not state.player.dead
        assert state.player.health == C.PLAYER_MAX_HEALTH

        for ent in state.level.entities:
            if ent.__class__.__name__ == "GoalTotem":
                state.player.pos = pygame.Vector2(ent.pos.x, ent.pos.y)
                state.player.rect.topleft = (int(ent.pos.x), int(ent.pos.y))
                state._check_goal_totem()
                break
        assert isinstance(game.next_state, ResultsState)

        print("Ape Adventure smoke test OK")
        return 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
