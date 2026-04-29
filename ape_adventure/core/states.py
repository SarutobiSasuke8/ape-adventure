"""State machine. Each state implements enter/handle/update/draw/exit."""
from __future__ import annotations

import math

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


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

class TitleState(State):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.font_big = pygame.font.SysFont("arial", 72, bold=True)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.t = 0.0

    def handle(self, snapshot: InputSnapshot) -> None:
        if snapshot.confirm or snapshot.start:
            self.game.change_state(LevelState(self.game))
        if snapshot.quit:
            self.game.running = False

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surf: pygame.Surface) -> None:
        w, h = surf.get_size()
        for y in range(h):
            t = y / h
            pygame.draw.line(surf, (
                int(18 * (1 - t) + 10 * t),
                int(64 * (1 - t) + 40 * t),
                int(38 * (1 - t) + 22 * t),
            ), (0, y), (w, y))

        # Animated vine
        vx = w // 2
        for i in range(8):
            vy = 80 + i * 28 + int(math.sin(self.t * 1.8 + i * 0.5) * 6)
            prev_vy = 80 + (i - 1) * 28 + int(math.sin(self.t * 1.8 + (i - 1) * 0.5) * 6)
            if i > 0:
                pygame.draw.line(surf, (50, 100, 30), (vx, prev_vy), (vx, vy), 3)
            pygame.draw.circle(surf, (60, 130, 40), (vx, vy), 4)

        bob = int(math.sin(self.t * 2.0) * 4)
        title = self.font_big.render("APE ADVENTURE", True, (250, 210, 90))
        shadow = self.font_big.render("APE ADVENTURE", True, (50, 25, 8))
        tr = title.get_rect(center=(w // 2, h // 2 - 60 + bob))
        surf.blit(shadow, tr.move(3, 3))
        surf.blit(title, tr)

        sub = self.font_med.render("Tangle Jungle — Vertical Slice", True, (180, 230, 150))
        surf.blit(sub, sub.get_rect(center=(w // 2, tr.bottom + 18)))

        if int(self.t * 2) % 2 == 0:
            prompt = self.font_small.render("Press ENTER or SPACE to play", True, (220, 220, 180))
            surf.blit(prompt, prompt.get_rect(center=(w // 2, h // 2 + 80)))

        hints = [
            "Arrows / WASD — Move    Space / Z — Jump (hold for higher)",
            "Shift — Run    X — Roll attack",
        ]
        for i, hint in enumerate(hints):
            txt = self.font_small.render(hint, True, (140, 180, 120))
            surf.blit(txt, txt.get_rect(center=(w // 2, h - 80 + i * 26)))


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------

class LevelState(State):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.level = None
        self.player = None
        self.camera = None
        self.renderer = None
        self.hud = None
        self.audio = None
        self.respawn_timer = 0.0
        self._paused = False
        self.banana_count = 0
        self.aape_collected: set[str] = set()
        self.level_timer = 0.0

    def enter(self) -> None:
        from ape_adventure.levels.level import build_test_level
        from ape_adventure.entities.player import Player
        from ape_adventure.core.camera import Camera
        from ape_adventure.render.renderer import Renderer
        from ape_adventure.render.hud import Hud
        from ape_adventure.audio.audio import AudioManager

        self.level = build_test_level()
        sp = self.level.spawn_point
        self.player = Player(sp.x, sp.y)
        self.camera = Camera(self.level.bounds)
        self.camera.snap_to(pygame.Vector2(sp.x + 14, sp.y + 22))
        self.renderer = Renderer(self.game.screen)
        self.hud = Hud()
        self.audio = AudioManager()

    def handle(self, snapshot: InputSnapshot) -> None:
        if snapshot.start:
            self._paused = not self._paused
        if snapshot.quit:
            self.game.change_state(TitleState(self.game))
            return
        if not self._paused and self.player and not self.player.dead:
            prev_on_ground = self.player.on_ground
            prev_state = self.player.state
            self.player.handle(snapshot)

    def update(self, dt: float) -> None:
        if self._paused:
            return

        self.level_timer += dt

        # Respawn delay
        if self.respawn_timer > 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self._respawn()
            return

        prev_on_ground = self.player.on_ground
        prev_state = self.player.state
        prev_vy = self.player.velocity.y

        self.player.update(dt, self.level)

        # SFX triggers on state transitions
        if not prev_on_ground and self.player.on_ground:
            self.audio.play("land")
        if prev_state != "jump" and self.player.state == "jump":
            self.audio.play("jump")
        if prev_state != "roll" and self.player.state == "roll":
            self.audio.play("roll")

        # Update all level entities
        alive_entities = []
        for ent in self.level.entities:
            ent.update(dt, self.level)
            if getattr(ent, "alive", True):
                alive_entities.append(ent)
        self.level.entities = alive_entities

        # Collision checks
        self._check_enemy_collisions()
        self._check_collectible_collisions()
        self._check_goal_totem()

        # Pit death
        if self.player.pos.y > self.level.bounds.height + 60:
            self._trigger_death()

        # Camera
        centre = pygame.Vector2(
            self.player.pos.x + self.player.rect.width * 0.5,
            self.player.pos.y + self.player.rect.height * 0.5,
        )
        self.camera.follow(centre, dt, self.player.facing)

        # HUD update
        self.hud.update(dt, self.banana_count, self.aape_collected, self.player.health)

    def _check_enemy_collisions(self) -> None:
        from ape_adventure.entities.enemies.snapper import Snapper

        pr = self.player.rect
        for ent in self.level.entities:
            if not isinstance(ent, Snapper) or ent._dying:
                continue
            if not pr.colliderect(ent.rect):
                continue

            # Stomp: player falling and landing on top half of enemy
            stomping = (
                self.player.velocity.y > 80
                and pr.bottom <= ent.rect.centery + 12
            )
            rolling = self.player.rolling_timer > 0

            if stomping or rolling:
                ent.die()
                self.audio.play("stomp_enemy")
                if stomping:
                    self.player.velocity.y = -380  # bounce up
            elif self.player.invuln_timer <= 0:
                self.player.health -= 1
                self.player.invuln_timer = C.PLAYER_INVULN_AFTER_HIT
                self.audio.play("player_hurt")
                # Knock back
                kb_dir = 1 if self.player.pos.x < ent.rect.centerx else -1
                self.player.velocity.x = -kb_dir * 180
                self.player.velocity.y = -250
                if self.player.health <= 0:
                    self._trigger_death()

    def _check_collectible_collisions(self) -> None:
        from ape_adventure.entities.collectibles.banana import Banana
        from ape_adventure.entities.collectibles.aape_letter import AapeLetter

        pr = self.player.rect
        for ent in self.level.entities:
            if isinstance(ent, Banana) and not ent.collected and pr.colliderect(ent.rect):
                ent.collected = True
                self.banana_count += 1
                self.audio.play("collect_banana")
                if self.banana_count % 100 == 0:
                    self.player.health = min(self.player.health + 1, C.PLAYER_MAX_HEALTH)
                    self.audio.play("extra_life")

            elif isinstance(ent, AapeLetter) and not ent.collected and pr.colliderect(ent.rect):
                ent.collected = True
                self.aape_collected.add(ent.letter)
                self.audio.play("collect_letter")
                if len(self.aape_collected) == 4:
                    self.player.health = min(self.player.health + 1, C.PLAYER_MAX_HEALTH)
                    self.audio.play("extra_life")

    def _check_goal_totem(self) -> None:
        from ape_adventure.entities.collectibles.goal_totem import GoalTotem

        for ent in self.level.entities:
            if isinstance(ent, GoalTotem) and not ent.touched:
                if self.player.rect.colliderect(ent.rect):
                    ent.touched = True
                    self.audio.play("goal_totem")
                    results = {
                        "bananas": self.banana_count,
                        "total_bananas": self.level.total_bananas,
                        "aape": self.aape_collected,
                        "time": self.level_timer,
                        "aape_complete": len(self.aape_collected) == 4,
                    }
                    self.game.change_state(ResultsState(self.game, results))

    def _trigger_death(self) -> None:
        self.player.dead = True
        self.player.health = max(0, self.player.health - 1)
        self.audio.play("player_hurt")
        self.respawn_timer = 1.2

    def _respawn(self) -> None:
        sp = self.level.spawn_point
        self.player.pos = pygame.Vector2(sp)
        self.player.rect.topleft = (int(sp.x), int(sp.y))
        self.player.velocity = pygame.Vector2(0, 0)
        self.player.on_ground = False
        self.player.dead = False
        self.player.invuln_timer = 1.5
        self.camera.snap_to(pygame.Vector2(sp.x + 14, sp.y + 22))

    def draw(self, surf: pygame.Surface) -> None:
        self.renderer.draw_frame(self.level, self.camera, [self.player] + self.level.entities)
        self.hud.draw(surf)
        if self._paused:
            self._draw_pause(surf)

    def _draw_pause(self, surf: pygame.Surface) -> None:
        ov = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        surf.blit(ov, (0, 0))
        font = pygame.font.SysFont("arial", 52, bold=True)
        txt = font.render("PAUSED", True, (250, 210, 90))
        surf.blit(txt, txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2)))
        small = pygame.font.SysFont("arial", 22)
        surf.blit(small.render("P — resume  |  Esc — title", True, (200, 230, 180)),
                  pygame.Rect(0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT).move(
                      C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 54
                  ).topleft)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

class ResultsState(State):
    def __init__(self, game, results: dict) -> None:
        super().__init__(game)
        self.results = results
        self.t = 0.0
        self.font_big = pygame.font.SysFont("arial", 52, bold=True)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 20)

    def handle(self, snapshot: InputSnapshot) -> None:
        if snapshot.confirm or snapshot.start:
            self.game.change_state(TitleState(self.game))

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surf: pygame.Surface) -> None:
        w, h = surf.get_size()

        # Dark overlay with jungle tint
        surf.fill((12, 34, 20))
        for y in range(h):
            t = y / h
            pygame.draw.line(surf, (
                int(12 + 8 * t), int(34 + 20 * t), int(20 + 10 * t)
            ), (0, y), (w, y))

        # Title
        bob = int(math.sin(self.t * 2.0) * 3)
        title = self.font_big.render("LEVEL CLEAR!", True, (250, 210, 90))
        surf.blit(title, title.get_rect(center=(w // 2, 80 + bob)))

        r = self.results
        mins = int(r["time"]) // 60
        secs = int(r["time"]) % 60
        lines = [
            (f"Time:     {mins:02d}:{secs:02d}", (200, 230, 200)),
            (f"Bananas:  {r['bananas']} / {r['total_bananas']}", (255, 220, 70)),
            (f"AAPE:     {'COMPLETE!' if r['aape_complete'] else f'{len(r[chr(97)+chr(97)+chr(112)+chr(101)])} / 4'}", (250, 200, 60) if r["aape_complete"] else (160, 130, 60)),
        ]
        # fix the AAPE display key
        aape_display = "COMPLETE!" if r["aape_complete"] else f"{len(r['aape'])} / 4"
        lines = [
            (f"Time:     {mins:02d}:{secs:02d}", (200, 230, 200)),
            (f"Bananas:  {r['bananas']} / {r['total_bananas']}", (255, 220, 70)),
            (f"AAPE:     {aape_display}", (250, 200, 60) if r["aape_complete"] else (160, 130, 60)),
        ]

        for i, (line, col) in enumerate(lines):
            txt = self.font_med.render(line, True, col)
            surf.blit(txt, txt.get_rect(center=(w // 2, 180 + i * 52)))

        # AAPE letter display
        letter_chars = ("A", "A", "P", "E")
        letter_keys = ("A1", "A2", "P", "E")
        lx = w // 2 - 80
        for key, char in zip(letter_keys, letter_chars):
            collected = key in r["aape"]
            col = (250, 200, 60) if collected else (60, 50, 30)
            pts = [(lx + 20, 340), (lx + 36, 356), (lx + 20, 372), (lx + 4, 356)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (200, 160, 40) if collected else (80, 65, 35), pts, 2)
            lbl = self.font_small.render(char, True, (40, 20, 8) if collected else (100, 80, 40))
            surf.blit(lbl, lbl.get_rect(center=(lx + 20, 356)))
            lx += 44

        if int(self.t * 2) % 2 == 0:
            prompt = self.font_small.render("Press ENTER to return to title", True, (180, 220, 160))
            surf.blit(prompt, prompt.get_rect(center=(w // 2, h - 60)))


# ---------------------------------------------------------------------------
# Placeholder states for later phases
# ---------------------------------------------------------------------------

class WorldMapState(State):
    """World node map — Phase 1.3."""


class PauseState(State):
    """Dedicated pause overlay — Phase 1.1 polish."""
