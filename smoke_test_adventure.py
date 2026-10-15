"""Headless smoke test for the Ape Adventure package.

Two phases:

1. Boot: construct the real ``Game`` (window, input, save, settings, title
   state), press Enter on the title screen and step the real frame loop into
   Tangle Jungle 1-1. Settings are redirected to a temp dir so nothing is
   written to the user's data folder.
2. Level: drive ``LevelState`` through movement, a death and respawn, and the
   goal totem into the results screen.

Run with ``python smoke_test_adventure.py``. Exits non-zero on failure.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot
from ape_escape.core.states import LevelState, ResultsState, TitleState


class _MemorySave:
    """In-memory stand-in for SaveData so the smoke test never writes to disk."""

    def __init__(self) -> None:
        self._times: dict[str, float] = {}

    def record_clear(self, level_id, time, bananas, aape) -> dict[str, bool]:
        new_time = level_id not in self._times or time < self._times[level_id]
        if new_time:
            self._times[level_id] = time
        return {"new_time": new_time, "new_bananas": True, "new_aape": True}

    def best_time(self, level_id):
        return self._times.get(level_id)


class FakeGame:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        self.next_state = None
        self.running = True
        self.save = _MemorySave()

    def change_state(self, new_state) -> None:
        self.next_state = new_state


def run_frames(state: LevelState, screen: pygame.Surface, snapshots: list[InputSnapshot]) -> None:
    for snap in snapshots:
        pygame.event.pump()
        state.handle(snap)
        state.update(1 / C.FPS)
        state.draw(screen)


def wait_for_audio(state) -> None:
    """Let the off-thread music build finish before pygame.quit().

    AudioManager generates the music loop on a daemon thread; quitting the
    mixer underneath it crashes the interpreter.
    """
    audio = getattr(state, "audio", None)
    ready = getattr(audio, "_music_ready", None)
    if ready is not None:
        assert ready.wait(timeout=60), "music loop did not finish building"


def step_real_game(game, events: list[pygame.event.Event] | None = None) -> None:
    """One iteration of ``Game.run`` without the clock, flip-loop or sys.exit."""
    if game.next_state is not None:
        game.state.exit()
        game.state = game.next_state
        game.next_state = None
        game.state.enter()
    pygame.event.pump()
    snapshot = game.input.poll(events or [])
    game.state.handle(snapshot)
    game.state.update(1 / C.FPS)
    game.state.draw(game.screen)
    pygame.display.flip()


def boot_real_game() -> None:
    from ape_escape.core.game import Game

    with tempfile.TemporaryDirectory() as tmp, mock.patch(
        "ape_escape.core.paths.user_data_dir", return_value=Path(tmp)
    ):
        game = Game()
        try:
            assert isinstance(game.state, TitleState), type(game.state).__name__
            assert game.screen.get_size() == (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
            for _ in range(30):
                step_real_game(game)
            assert isinstance(game.state, TitleState)

            enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            step_real_game(game, [enter])
            assert isinstance(game.next_state, LevelState), "Enter on title did not start a level"
            for _ in range(60):
                step_real_game(game)
            assert isinstance(game.state, LevelState), type(game.state).__name__
            assert game.state.level is not None and game.state.level.level_id == "1-1"
            assert game.running
            assert not any(Path(tmp).iterdir()), "boot wrote to the user data dir"
        finally:
            # No pygame.quit() here: some modules cache Font objects at module
            # level, and those crash if reused after a quit/init cycle. main()
            # quits once at the end.
            wait_for_audio(game.state)
    print("Ape Adventure boot OK")


def main() -> int:
    boot_real_game()

    pygame.init()
    game = FakeGame()
    state = LevelState(game)
    state.enter()

    try:
        assert state.player is not None
        assert state.level is not None
        assert state.player.health == C.PLAYER_MAX_HEALTH

        # The authored Tangle Jungle 1-1 map should load via the pytmx loader
        # (not fall back to the test playground).
        assert state.level.level_id == "1-1", f"expected tmx level, got {state.level.level_id!r}"
        assert state.level.tile_grid is not None
        assert state.level.total_bananas > 0
        assert state.level.total_letters == 4
        assert any(e.__class__.__name__ == "GoalTotem" for e in state.level.entities)

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
        wait_for_audio(state)
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
