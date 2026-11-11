"""World 1 completion: King Saurus coconut phase, checkpoints, arena camera, music.

The coconut volley is the boss's second phase: it starts after his second
hit. These tests prove it fires only then, that a coconut really hurts a
player who stays put, and that stepping out of its shadow dodges it.
Checkpoint tests prove a death after a checkpoint respawns there with the
usual full-health refill, and that a death before one still uses the start.
"""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot as S
from ape_escape.entities.enemies.king_saurus import COCONUT_PHASE, KingSaurus
from ape_escape.entities.hazards.coconut import Coconut
from ape_escape.entities.props.checkpoint import Checkpoint
from tests import playthrough as pt

TILE = C.TILE_SIZE


class _Case(unittest.TestCase):
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

    def step(self, st, snap: S | None = None, n: int = 1) -> None:
        for _ in range(n):
            st.handle(snap or S())
            st.update(pt.DT)

    @staticmethod
    def place(st, centre_x: float, bottom: float) -> None:
        p = st.player
        p.pos = pygame.Vector2(centre_x - p.rect.width / 2, bottom - p.rect.height)
        p.rect.topleft = (int(p.pos.x), int(p.pos.y))
        p.velocity = pygame.Vector2(0, 0)


# ---------------------------------------------------------------------------
# King Saurus: coconut phase
# ---------------------------------------------------------------------------

class CoconutPhaseTest(_Case):
    def setUp(self) -> None:
        self.game, self.st = self.load(3)
        self.boss = next(e for e in self.st.level.entities if isinstance(e, KingSaurus))
        # Only the boss and his coconuts: no corridor Snapper in these tests.
        self.st.level.entities = [e for e in self.st.level.entities if type(e).__name__ != "Snapper"]
        self.ledge_x = self.boss.arena_left + 2 * TILE + TILE / 2
        self.place(self.st, self.ledge_x, 14 * TILE)  # on the left safe ledge
        self.step(self.st, n=5)

    def coconuts(self) -> list[Coconut]:
        return [e for e in self.st.level.entities if isinstance(e, Coconut)]

    def hit(self) -> None:
        """Land one stomp the way the arena allows: only while he is dazed."""
        self.boss.state = "dazed"
        self.assertTrue(self.boss.on_stomp())

    def run_until_not(self, state: str, limit: int = 300) -> None:
        for _ in range(limit):
            if self.boss.state != state:
                return
            self.step(self.st)
        self.fail(f"boss stuck in {state}")

    def to_final_phase(self) -> None:
        self.hit()
        self.run_until_not("hurt")
        self.hit()
        self.assertEqual((self.boss.hp, self.boss.phase), (1, COCONUT_PHASE))
        self.run_until_not("hurt")

    def test_no_coconuts_before_the_second_hit(self) -> None:
        self.hit()
        self.run_until_not("hurt")
        self.assertEqual(self.boss.state, "telegraph")
        self.step(self.st, n=120)
        self.assertEqual(self.coconuts(), [])
        self.assertEqual(self.boss.volleys, 0)

    def test_roar_drops_coconuts_after_the_second_hit(self) -> None:
        self.to_final_phase()
        self.assertEqual(self.boss.state, "roar")
        self.step(self.st)
        nuts = self.coconuts()
        self.assertGreaterEqual(len(nuts), 1)
        self.assertEqual(self.boss.volleys, 1)
        # The tell: every coconut starts hanging in the canopy, harmless, with
        # its landing spot (shadow) known; one is aimed at the player.
        for c in nuts:
            self.assertEqual(c.state, "warn")
            self.assertFalse(c.harmful)
            self.assertIsNotNone(c.ground_y)
        self.assertTrue(any(abs(c.rect.centerx - self.st.player.rect.centerx) < TILE for c in nuts))
        # He cannot be stomped while roaring, and touching him hurts.
        self.assertTrue(self.boss.harmful)
        self.assertFalse(self.boss.vulnerable)
        self.st.draw(self.screen)

    def test_coconut_hits_a_player_who_stays_put(self) -> None:
        self.to_final_phase()
        start = self.st.player.health
        for _ in range(240):
            self.step(self.st)
            if self.st.player.health < start:
                break
        self.assertEqual(self.st.player.health, start - 1, "standing in the shadow should cost a hit")

    def test_coconut_can_be_dodged_by_leaving_its_shadow(self) -> None:
        self.to_final_phase()
        self.step(self.st)
        self.assertTrue(self.coconuts())
        start = self.st.player.health
        arena = self.boss.arena_left
        script = pt.hold_ledge_dodging(
            self.st, self.ledge_x, lo=arena - 6 * TILE, hi=arena + 4 * TILE - 20,
            until=lambda: not pt.live_coconuts(self.st), limit=300)
        for snap in script:
            st = self.st
            st.handle(snap)
            st.update(pt.DT)
        self.assertEqual(self.st.player.health, start, "dodging should avoid every coconut")
        self.assertEqual(pt.live_coconuts(self.st), [])

    def test_final_stomp_still_lands_after_the_roar(self) -> None:
        self.to_final_phase()
        # Let the roar and its coconuts play out, then wait for the crash.
        arena = self.boss.arena_left
        for snap in pt.hold_ledge_dodging(
                self.st, self.ledge_x, lo=arena - 6 * TILE, hi=arena + 4 * TILE - 20,
                until=lambda: self.boss.state == "dazed", limit=900):
            self.st.handle(snap)
            self.st.update(pt.DT)
        self.assertTrue(self.boss.vulnerable)
        self.assertTrue(self.boss.on_stomp())
        self.assertEqual(self.boss.state, "defeated")

    def test_boss_waits_until_the_player_enters_the_arena(self) -> None:
        game, st = self.load(3)
        boss = next(e for e in st.level.entities if isinstance(e, KingSaurus))
        st.level.entities = [e for e in st.level.entities if type(e).__name__ != "Snapper"]
        self.step(st, n=180)  # player still at the corridor spawn
        self.assertEqual(boss.state, "idle")
        self.place(st, boss.arena_left + 2 * TILE, 14 * TILE)
        self.step(st, n=3)
        self.assertEqual(boss.state, "telegraph")

    def test_camera_locks_to_the_arena(self) -> None:
        self.step(self.st, n=120)
        self.assertAlmostEqual(self.st.camera.offset.x, self.boss.arena_left, delta=2.0)


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------

class CheckpointTest(_Case):
    def checkpoint(self, st) -> Checkpoint:
        cps = st.level.checkpoints()
        self.assertEqual(len(cps), 1)
        return cps[0]

    def respawn_after_death(self, st) -> None:
        st._trigger_death()
        self.step(st, n=int(1.4 * C.FPS))
        self.assertFalse(st.player.dead)

    def test_checkpoints_sit_between_spawn_and_goal(self) -> None:
        for index in (1, 2, 3):
            with self.subTest(level=index):
                _, st = self.load(index)
                cp = self.checkpoint(st)
                totem = next(e for e in st.level.entities if type(e).__name__ == "GoalTotem")
                self.assertLess(st.level.spawn_point.x + 4 * TILE, cp.rect.centerx)
                self.assertLess(cp.rect.centerx, totem.rect.centerx)

    def test_pit_death_after_checkpoint_respawns_there(self) -> None:
        """1-2: walk through the checkpoint, fall into gap C, come back at the post."""
        _, st = self.load(1)
        cp = self.checkpoint(st)
        self.place(st, cp.rect.centerx - 40, 16 * TILE)   # just past the small pit
        died = False
        for _ in range(600):
            self.step(st, S(move_x=1.0))
            if st.player.dead:
                died = True
                break
        self.assertTrue(cp.active, "walked past without reaching the checkpoint")
        self.assertTrue(died, "never fell into gap C")
        self.step(st, n=int(1.4 * C.FPS))
        p = st.player
        self.assertFalse(p.dead)
        self.assertEqual(st.deaths, 1)
        self.assertAlmostEqual(p.rect.centerx, cp.rect.centerx, delta=2)
        self.assertEqual(p.health, C.PLAYER_MAX_HEALTH)   # same refill as before
        self.step(st, n=30)
        self.assertEqual(p.rect.bottom, cp.rect.bottom)   # standing on the ground at the post

    def test_death_after_checkpoint_respawns_there_in_1_3_and_1_4(self) -> None:
        for index in (2, 3):
            with self.subTest(level=index):
                _, st = self.load(index)
                cp = self.checkpoint(st)
                self.place(st, cp.rect.centerx, cp.rect.bottom)
                self.step(st)
                self.assertIs(st.checkpoint, cp)
                self.place(st, cp.rect.centerx + 5 * TILE, cp.rect.bottom)  # move on
                self.step(st, n=5)
                self.respawn_after_death(st)
                self.assertAlmostEqual(st.player.rect.centerx, cp.rect.centerx, delta=2)
                self.assertEqual(st.player.health, C.PLAYER_MAX_HEALTH)

    def test_death_before_checkpoint_respawns_at_level_start(self) -> None:
        _, st = self.load(1)
        cp = self.checkpoint(st)
        self.step(st, S(move_x=1.0), n=30)
        self.assertFalse(cp.active)
        self.respawn_after_death(st)
        self.assertEqual(st.player.pos, st.level.spawn_point)

    def test_latest_checkpoint_reached_wins(self) -> None:
        _, st = self.load(1)
        first = self.checkpoint(st)
        later = Checkpoint(first.pos.x + 20 * TILE, first.pos.y)
        st.level.entities.append(later)
        for cp in (first, later):
            self.place(st, cp.rect.centerx, cp.rect.bottom)
            self.step(st)
        self.assertIs(st.checkpoint, later)
        # Walking back over an already-reached checkpoint does not move it.
        self.place(st, first.rect.centerx, first.rect.bottom)
        self.step(st)
        self.assertIs(st.checkpoint, later)
        st.draw(self.screen)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Per-level music
# ---------------------------------------------------------------------------

class MusicSelectionTest(_Case):
    def test_each_level_asks_for_its_own_music_key(self) -> None:
        from ape_escape.levels.world_data import ALL_WORLDS

        for i, entry in enumerate(ALL_WORLDS[0].levels):
            with self.subTest(level=entry.id):
                _, st = self.load(i)
                self.assertEqual(st.audio.music_key, entry.music_key)

    def test_boss_style_differs_and_unknown_keys_fall_back(self) -> None:
        from ape_escape.audio import audio as A

        self.assertNotEqual(A.music_style("king_saurus"), A.music_style("tangle_jungle"))
        self.assertEqual(A.music_style("no_such_track"), A.music_style("tangle_jungle"))
        mgr = A.AudioManager("king_saurus")
        try:
            self.assertEqual(mgr.music_key, "king_saurus")
        finally:
            mgr.shutdown()
        mgr = A.AudioManager("no_such_track")
        try:
            self.assertEqual(mgr.music_key, A.DEFAULT_MUSIC_KEY)
        finally:
            mgr.shutdown()
