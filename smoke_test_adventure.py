"""Headless smoke test for the Ape Adventure package.

Two phases:

1. Boot: construct the real ``Game`` (window, input, save, settings, title
   state), press Enter on the title screen and step the real frame loop into
   Tangle Jungle 1-1, then quit through ``Game.run`` straight away, while the
   music loop is still building. Settings are redirected to a temp dir so
   nothing is written to the user's data folder.
2. Level: in a fresh pygame session (quit + init after phase 1), drive
   ``LevelState`` through movement, a death and respawn, and the goal totem
   into the results screen.

Both phases render an AAPE letter, so a font cached across sessions fails here.

Run with ``python smoke_test_adventure.py``. Exits non-zero on failure.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
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


def draw_letter(state: LevelState, screen: pygame.Surface) -> None:
    """Render one AAPE letter directly, whether or not it is on camera.

    The letter's font must belong to the current pygame session; a font kept
    from an earlier session crashes after quit + init.
    """
    from ape_escape.entities.collectibles.aape_letter import AapeLetter

    letter = next(e for e in state.level.entities if isinstance(e, AapeLetter))
    letter.draw(screen, state.camera)


def background_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t is not threading.main_thread()]


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
            for _ in range(5):
                step_real_game(game)
            assert isinstance(game.state, LevelState), type(game.state).__name__
            assert game.state.level is not None and game.state.level.level_id == "1-1"
            assert game.running
            draw_letter(game.state, game.screen)
            assert not any(Path(tmp).iterdir()), "boot wrote to the user data dir"

            # Quit early, through the real loop, while the music loop is
            # still being generated on its background thread.
            assert not game.state.audio._music_ready.is_set(), "music finished too soon to test an early quit"
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            try:
                game.run()
            except SystemExit as exc:
                assert exc.code == 0, exc.code
            else:
                raise AssertionError("Game.run() returned without sys.exit")
            assert not pygame.get_init(), "Game.run() did not quit pygame"
            leftover = background_threads()
            assert not leftover, f"threads still running after quit: {leftover}"
        except BaseException:
            pygame.quit()
            raise
    print("Ape Adventure boot + early quit OK")


def main() -> int:
    boot_real_game()

    # Second pygame session: restart after the quit above.
    pygame.init()
    game = FakeGame()
    state = LevelState(game)
    state.enter()

    try:
        draw_letter(state, game.screen)
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
        state.exit()
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
