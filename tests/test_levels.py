"""Tangle Jungle levels 1-1 to 1-4: load, completability, mechanics, progression.

Completability is proven by scripted playthroughs (tests/playthrough.py) that
drive the real LevelState to each goal totem. The mechanic tests check that
each new level's mechanic is actually needed, not just present.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot as S
from ape_escape.core.states import LevelState, ResultsState, TitleState
from ape_escape.levels.world_data import ALL_WORLDS
from tests import playthrough as pt

LEVELS = ALL_WORLDS[0].levels
LEVELS_DIR = Path(__file__).resolve().parent.parent / "ape_escape" / "levels"
TILE = C.TILE_SIZE


def _kinds(level) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in level.entities:
        out[type(e).__name__] = out.get(type(e).__name__, 0) + 1
    return out


class _PygameCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def load(self, index: int):
        game = pt.HarnessGame(self.screen)
        st = pt.make_level_state(game, index)
        self.addCleanup(st.exit)
        return game, st

    def frames(self, st, snaps) -> None:
        for snap in snaps:
            st.handle(snap)
            st.update(pt.DT)


class LevelLoadTest(_PygameCase):
    def test_every_level_has_an_authored_map(self) -> None:
        for entry in LEVELS:
            with self.subTest(level=entry.id):
                self.assertTrue((LEVELS_DIR / entry.tmx_path).exists(), entry.tmx_path)

    def test_each_level_loads_from_tmx(self) -> None:
        for i, entry in enumerate(LEVELS):
            with self.subTest(level=entry.id):
                _, st = self.load(i)
                self.assertEqual(st.level.level_id, entry.id)  # not the test playground
                self.assertEqual(st.level.music_key, entry.music_key)
                kinds = _kinds(st.level)
                self.assertEqual(kinds.get("GoalTotem"), 1)
                self.assertGreater(st.level.total_bananas, 0)
                st.draw(self.screen)

    def test_new_level_contents(self) -> None:
        _, s2 = self.load(1)
        k2 = _kinds(s2.level)
        self.assertEqual(k2.get("Vine"), 5)
        self.assertEqual(s2.level.total_letters, 4)

        _, s3 = self.load(2)
        self.assertEqual(s3.level.total_letters, 4)
        self.assertGreaterEqual(_kinds(s3.level).get("Snapper", 0), 6)

        _, s4 = self.load(3)
        k4 = _kinds(s4.level)
        self.assertEqual(k4.get("KingSaurus"), 1)
        totem = next(e for e in s4.level.entities if type(e).__name__ == "GoalTotem")
        self.assertTrue(totem.locked)


class CompletabilityTest(_PygameCase):
    """Scripted runs: each level is finished without dying."""

    def _assert_completes(self, index: int) -> None:
        res = pt.play_level(index)
        self.assertTrue(res.completed, res.summary())
        self.assertEqual(res.deaths, 0, res.summary())

    def test_1_1_completes(self) -> None:
        self._assert_completes(0)

    def test_1_2_completes(self) -> None:
        self._assert_completes(1)

    def test_1_3_completes(self) -> None:
        self._assert_completes(2)

    def test_1_4_completes(self) -> None:
        self._assert_completes(3)


class MechanicRequiredTest(_PygameCase):
    def test_1_2_vine_gap_cannot_be_jumped(self) -> None:
        """A full running jump at gap A's edge, ignoring the vine, falls in."""
        _, st = self.load(1)
        st.level.entities = [e for e in st.level.entities if type(e).__name__ != "Vine"]
        script = pt.jump_at(st, 16 * TILE - 12, hold=60)
        for _ in range(240):
            try:
                snap = next(script)
            except StopIteration:
                snap = S(move_x=1.0, run=True, jump_held=True)
            st.handle(snap)
            st.update(pt.DT)
            if st.player.dead:
                break
        self.assertTrue(st.player.dead, f"cleared gap A without a vine (x={st.player.rect.centerx})")

    def test_1_3_log_blocks_a_standing_player(self) -> None:
        """Walking or jumping into log 1 without rolling never gets through."""
        _, st = self.load(2)
        log_start = 14 * TILE
        for i in range(300):
            st.handle(S(move_x=1.0, run=True, jump=(i % 40 == 0), jump_held=True))
            st.update(pt.DT)
        self.assertLess(st.player.rect.right, log_start + 2)
        self.assertFalse(st.player.crouched)

    def test_1_3_roll_fits_under_log_and_crawls_out(self) -> None:
        _, st = self.load(2)
        while st.player.rect.right < 14 * TILE - 24:   # up to the mouth of log 1
            st.handle(S(move_x=1.0))
            st.update(pt.DT)
        seen_crawl = False
        for _ in range(300):
            st.handle(S(move_x=1.0, roll=st.player.rolling_timer <= 0 and not st.player.crouched))
            st.update(pt.DT)
            seen_crawl |= st.player.state == "crawl"
            if st.player.rect.left > 20 * TILE and not st.player.crouched:
                break
        self.assertGreater(st.player.rect.left, 20 * TILE, "did not get through log 1")
        self.assertTrue(seen_crawl, "never crawled under the log after the roll ended")
        self.assertEqual(st.player.rect.height, C.PLAYER_STAND_HEIGHT)

    def test_1_4_totem_locked_while_boss_alive(self) -> None:
        game, st = self.load(3)
        totem = next(e for e in st.level.entities if type(e).__name__ == "GoalTotem")
        st.player.pos = pygame.Vector2(totem.pos)
        st.player.rect.topleft = (int(totem.pos.x), int(totem.pos.y))
        st._check_goal_totem()
        self.assertIsNone(game.next_state)

    def test_1_4_roll_does_not_hurt_boss(self) -> None:
        _, st = self.load(3)
        boss = next(e for e in st.level.entities if type(e).__name__ == "KingSaurus")
        self.assertFalse(boss.on_roll())
        boss.state = "charge"
        self.assertFalse(boss.on_stomp(), "stomp only counts while dazed")
        self.assertEqual(boss.hp, 3)
        boss.state = "dazed"
        self.assertTrue(boss.on_stomp())
        self.assertEqual((boss.hp, boss.phase, boss.state), (2, 2, "hurt"))


class ProgressionTest(_PygameCase):
    def test_results_lead_to_next_level_then_title(self) -> None:
        for i, entry in enumerate(LEVELS):
            with self.subTest(level=entry.id):
                game = pt.HarnessGame(self.screen)
                res = ResultsState(game, {
                    "level_id": entry.id, "bananas": 0, "total_bananas": 1, "aape": set(),
                    "time": 1.0, "aape_complete": False, "level_index": i,
                })
                res.draw(self.screen)
                res.handle(S(confirm=True))
                if i + 1 < len(LEVELS):
                    self.assertIsInstance(game.next_state, LevelState)
                    self.assertEqual(game.next_state.level_index, i + 1)
                else:
                    self.assertIsInstance(game.next_state, TitleState)

    def test_full_world_run_chains_through_results(self) -> None:
        """Play 1-1 to 1-4 back to back, following ResultsState to each next level."""
        game = pt.HarnessGame(self.screen)
        index = 0
        cleared = []
        while True:
            res = pt.play_level(index)
            self.assertTrue(res.completed, res.summary())
            cleared.append(res.level_id)
            results = ResultsState(game, {
                "level_id": res.level_id, "bananas": res.bananas, "total_bananas": res.total_bananas,
                "aape": set(), "time": res.seconds, "aape_complete": False, "level_index": index,
            })
            game.next_state = None
            results.handle(S(confirm=True))
            if isinstance(game.next_state, TitleState):
                break
            self.assertIsInstance(game.next_state, LevelState)
            index = game.next_state.level_index
        self.assertEqual(cleared, [lv.id for lv in LEVELS])

    def test_restart_keeps_the_current_level(self) -> None:
        game, st = self.load(2)
        st.restart()
        self.assertIsInstance(game.next_state, LevelState)
        self.assertEqual(game.next_state.level_index, 2)


if __name__ == "__main__":
    unittest.main()
