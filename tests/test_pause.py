"""Pause menu state: Esc / P toggling, menu actions, live settings."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ape_escape.core import constants as C
from ape_escape.core import pause as PM
from ape_escape.core.input import Input, InputSnapshot
from ape_escape.core.states import GameplayState, LevelState, TitleState
from ape_escape.data.settings import Settings


class _MemorySave:
    def record_clear(self, *args, **kwargs):
        return {"new_time": False, "new_bananas": False, "new_aape": False}

    def best_time(self, level_id):
        return None


class FakeGame:
    def __init__(self, settings: Settings) -> None:
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        self.next_state = None
        self.running = True
        self.save = _MemorySave()
        self.settings = settings

    def change_state(self, new_state) -> None:
        self.next_state = new_state


DT = 1 / C.FPS
PAUSE = InputSnapshot(pause=True)
DOWN = InputSnapshot(down=True)
UP = InputSnapshot(up=True)
LEFT = InputSnapshot(left=True)
RIGHT = InputSnapshot(right=True)
CONFIRM = InputSnapshot(confirm=True)
IDLE = InputSnapshot()


class InputMappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _poll(self, key: int) -> InputSnapshot:
        ev = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0)
        return Input().poll([ev])

    def test_escape_and_p_both_pause(self) -> None:
        self.assertTrue(self._poll(pygame.K_ESCAPE).pause)
        self.assertTrue(self._poll(pygame.K_p).pause)
        self.assertFalse(self._poll(pygame.K_RETURN).pause)

    def test_arrow_keys_navigate(self) -> None:
        self.assertTrue(self._poll(pygame.K_UP).up)
        self.assertTrue(self._poll(pygame.K_DOWN).down)
        self.assertTrue(self._poll(pygame.K_LEFT).left)
        self.assertTrue(self._poll(pygame.K_RIGHT).right)


class PauseMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings_path = Path(self._tmp.name) / "settings.json"
        self.game = FakeGame(Settings.load(self.settings_path))
        self.state = LevelState(self.game)
        self.state.enter()

    def tearDown(self) -> None:
        self.state.exit()
        self._tmp.cleanup()

    def frame(self, snap: InputSnapshot) -> None:
        self.state.handle(snap)
        self.state.update(DT)
        self.state.draw(self.game.screen)

    def test_level_is_a_gameplay_state(self) -> None:
        self.assertIsInstance(self.state, GameplayState)

    def test_pause_freezes_and_resumes(self) -> None:
        self.frame(IDLE)
        self.assertFalse(self.state.paused)
        self.frame(PAUSE)
        self.assertTrue(self.state.paused)

        timer = self.state.level_timer
        pos = pygame.Vector2(self.state.player.pos)
        for _ in range(30):
            self.frame(InputSnapshot(move_x=1.0, run=True))
        self.assertEqual(self.state.level_timer, timer)
        self.assertEqual(self.state.player.pos, pos)

        self.frame(PAUSE)  # Esc / P again resumes
        self.assertFalse(self.state.paused)
        self.frame(IDLE)
        self.assertGreater(self.state.level_timer, timer)

    def test_resume_item(self) -> None:
        self.frame(PAUSE)
        self.frame(CONFIRM)  # first item is Resume
        self.assertFalse(self.state.paused)

    def test_restart_item(self) -> None:
        self.frame(PAUSE)
        self.frame(DOWN)
        self.frame(CONFIRM)
        self.assertIsInstance(self.game.next_state, LevelState)
        self.assertIsNot(self.game.next_state, self.state)

    def test_quit_to_title_item(self) -> None:
        self.frame(PAUSE)
        self.frame(UP)  # wraps to the last item
        self.frame(CONFIRM)
        self.assertIsInstance(self.game.next_state, TitleState)

    def test_quit_does_not_happen_on_escape_alone(self) -> None:
        self.frame(PAUSE)
        self.assertIsNone(self.game.next_state)

    def test_settings_page_changes_and_persists(self) -> None:
        self.frame(PAUSE)
        self.frame(DOWN)
        self.frame(DOWN)
        self.frame(CONFIRM)  # Settings
        self.assertEqual(self.state.pause_menu.page, "settings")

        start_music = self.game.settings.music_volume
        self.frame(LEFT)
        self.frame(LEFT)
        self.assertAlmostEqual(self.game.settings.music_volume, round(start_music - 0.2, 2))
        self.assertAlmostEqual(self.state.audio.music_volume, self.game.settings.music_volume)

        self.frame(DOWN)
        self.frame(LEFT)  # SFX volume down
        self.assertAlmostEqual(self.state.audio.sfx_volume, self.game.settings.sfx_volume)

        self.frame(DOWN)
        self.frame(CONFIRM)  # Reduced motion on
        self.assertTrue(self.game.settings.reduced_motion)
        self.assertTrue(self.state.hud.reduced_motion)

        on_disk = Settings.load(self.settings_path)
        self.assertEqual(on_disk.to_dict(), self.game.settings.to_dict())

        self.frame(PAUSE)  # Esc / P in settings goes back, not out
        self.assertTrue(self.state.paused)
        self.assertEqual(self.state.pause_menu.page, "main")
        self.assertEqual(PM.MAIN_ITEMS[self.state.pause_menu.index], "Settings")

    def test_reopening_pause_starts_on_main_page(self) -> None:
        self.frame(PAUSE)
        self.frame(DOWN)
        self.frame(DOWN)
        self.frame(CONFIRM)
        self.state.set_paused(False)
        self.frame(PAUSE)
        self.assertEqual(self.state.pause_menu.page, "main")
        self.assertEqual(self.state.pause_menu.index, 0)

    def test_reduced_motion_disables_screen_shake(self) -> None:
        self.state._trigger_shake(5.0, 0.3)
        self.assertGreater(self.state._shake_timer, 0)

        self.game.settings.reduced_motion = True
        self.state.on_settings_changed()
        self.assertEqual(self.state._shake_timer, 0)
        self.state._trigger_shake(5.0, 0.3)
        self.assertEqual(self.state._shake_timer, 0)
        self.frame(IDLE)
        self.assertEqual((self.state._shake_x, self.state._shake_y), (0, 0))


if __name__ == "__main__":
    unittest.main()
