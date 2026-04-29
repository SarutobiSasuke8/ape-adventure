"""State machine. Each state implements enter/handle/update/draw/exit."""
from __future__ import annotations

import math
import random

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot


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
        from ape_escape.levels.level import build_test_level
        from ape_escape.entities.player import Player
        from ape_escape.core.camera import Camera
        from ape_escape.render.renderer import Renderer
        from ape_escape.render.hud import Hud
        from ape_escape.audio.audio import AudioManager

        self.level = build_test_level()
        sp = self.level.spawn_point
        self.player = Player(sp.x, sp.y)
        self.camera = Camera(self.level.bounds)
        self.camera.snap_to(pygame.Vector2(sp.x + 14, sp.y + 22))
        self.renderer = Renderer(self.game.screen)
        self.hud = Hud()
        self.audio = AudioManager()
        from ape_escape.render.particles import ParticleSystem
        self.particles = ParticleSystem()
        # Juice state
        self._shake_timer:     float = 0.0
        self._shake_intensity: float = 0.0
        self._shake_x:         int   = 0
        self._shake_y:         int   = 0
        self._hit_pause_timer: float = 0.0
        self._run_dust_timer:  float = 0.0

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

        # --- Screen shake: update offset every frame regardless of pause/freeze ---
        if self._shake_timer > 0:
            self._shake_timer = max(0.0, self._shake_timer - dt)
            fade = self._shake_timer / max(0.001, self._shake_timer + dt)  # decay
            mag = int(self._shake_intensity * (0.3 + 0.7 * fade))
            self._shake_x = random.randint(-mag, mag)
            self._shake_y = random.randint(-mag, mag)
        else:
            self._shake_x = 0
            self._shake_y = 0

        # --- Hit-pause: freeze world updates for a short window ---
        if self._hit_pause_timer > 0:
            self._hit_pause_timer = max(0.0, self._hit_pause_timer - dt)
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

        # SFX + particle triggers on state transitions
        foot_x = self.player.pos.x + self.player.rect.width * 0.5
        foot_y = self.player.pos.y + self.player.rect.height

        if not prev_on_ground and self.player.on_ground:
            self.audio.play("land")
            self.particles.emit("dust", foot_x, foot_y, count=6)

        if prev_state != "jump" and self.player.state == "jump":
            self.audio.play("jump")
            self.particles.emit("leaf", foot_x, foot_y, count=4)

        if prev_state != "roll" and self.player.state == "roll":
            self.audio.play("roll")
            self.particles.emit("dust", foot_x, foot_y, count=5)

        # Run dust trail
        if self.player.state == "run":
            self._run_dust_timer -= dt
            if self._run_dust_timer <= 0:
                self.particles.emit("dust", foot_x, foot_y, count=2)
                self._run_dust_timer = 0.10

        self.particles.update(dt)

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
        self.audio.poll_music()
        centre = pygame.Vector2(
            self.player.pos.x + self.player.rect.width * 0.5,
            self.player.pos.y + self.player.rect.height * 0.5,
        )
        self.camera.follow(centre, dt, self.player.facing)

        # HUD update
        self.hud.update(dt, self.banana_count, self.aape_collected, self.player.health)

    # ------------------------------------------------------------------
    # Juice helpers
    # ------------------------------------------------------------------

    def _trigger_shake(self, intensity: float, duration: float) -> None:
        """Start (or strengthen) a screen-shake effect."""
        if intensity >= self._shake_intensity or self._shake_timer <= 0:
            self._shake_intensity = intensity
            self._shake_timer = duration

    def _trigger_hit_pause(self, duration: float = 0.055) -> None:
        """Freeze game updates for *duration* seconds (a few frames)."""
        self._hit_pause_timer = max(self._hit_pause_timer, duration)

    # ------------------------------------------------------------------

    def _check_enemy_collisions(self) -> None:
        from ape_escape.entities.enemies.enemy import Enemy

        pr = self.player.rect
        for ent in self.level.entities:
            if not isinstance(ent, Enemy):
                continue
            if getattr(ent, "_dying", False):
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
                self._trigger_hit_pause(0.055)
                self._trigger_shake(3.0, 0.18)
                self.particles.emit("puff", float(ent.rect.centerx), float(ent.rect.centery), count=7)
                if stomping:
                    self.player.velocity.y = -380  # bounce up
            elif self.player.invuln_timer <= 0:
                self.player.health -= 1
                self.player.invuln_timer = C.PLAYER_INVULN_AFTER_HIT
                self.audio.play("player_hurt")
                self._trigger_hit_pause(0.07)
                self._trigger_shake(5.0, 0.35)
                # Knock back
                kb_dir = 1 if self.player.pos.x < ent.rect.centerx else -1
                self.player.velocity.x = -kb_dir * 180
                self.player.velocity.y = -250
                if self.player.health <= 0:
                    self._trigger_death(play_hurt_sound=False)

    def _check_collectible_collisions(self) -> None:
        from ape_escape.entities.collectibles.banana import Banana
        from ape_escape.entities.collectibles.aape_letter import AapeLetter

        pr = self.player.rect
        for ent in self.level.entities:
            if isinstance(ent, Banana) and not ent.collected and pr.colliderect(ent.rect):
                ent.collected = True
                self.banana_count += 1
                self.audio.play("collect_banana")
                self.particles.emit("sparkle", float(ent.rect.centerx), float(ent.rect.centery), count=6)
                if self.banana_count % 100 == 0:
                    self.player.health = min(self.player.health + 1, C.PLAYER_MAX_HEALTH)
                    self.audio.play("extra_life")

            elif isinstance(ent, AapeLetter) and not ent.collected and pr.colliderect(ent.rect):
                ent.collected = True
                self.aape_collected.add(ent.letter)
                self.audio.play("collect_letter")
                self.particles.emit("sparkle", float(ent.rect.centerx), float(ent.rect.centery), count=12)
                if len(self.aape_collected) == 4:
                    self.player.health = min(self.player.health + 1, C.PLAYER_MAX_HEALTH)
                    self.audio.play("extra_life")

    def _check_goal_totem(self) -> None:
        from ape_escape.entities.collectibles.goal_totem import GoalTotem

        for ent in self.level.entities:
            if isinstance(ent, GoalTotem) and not ent.touched:
                if self.player.rect.colliderect(ent.rect):
                    ent.touched = True
                    self.audio.play("goal_totem")
                    # Persist the clear — get back "new record" flags
                    rec_flags = self.game.save.record_clear(
                        self.level.level_id,
                        self.level_timer,
                        self.banana_count,
                        self.aape_collected,
                    )
                    results = {
                        "level_id": self.level.level_id,
                        "bananas": self.banana_count,
                        "total_bananas": self.level.total_bananas,
                        "aape": self.aape_collected,
                        "time": self.level_timer,
                        "aape_complete": len(self.aape_collected) == 4,
                        "new_time": rec_flags["new_time"],
                        "new_bananas": rec_flags["new_bananas"],
                        "best_time": self.game.save.best_time(self.level.level_id),
                    }
                    self.game.change_state(ResultsState(self.game, results))

    def _trigger_death(self, play_hurt_sound: bool = True) -> None:
        if self.player.dead:
            return
        self.player.dead = True
        self.player.health = 0
        self.player.velocity = pygame.Vector2(0, 0)
        self.player.rolling_timer = 0.0
        self.player.jump_buffer_timer = 0.0
        self.player.coyote_timer = 0.0
        if play_hurt_sound:
            self.audio.play("player_hurt")
        self._trigger_shake(7.0, 0.50)
        self.respawn_timer = 1.2

    def _respawn(self) -> None:
        sp = self.level.spawn_point
        self.player.pos = pygame.Vector2(sp)
        self.player.rect.topleft = (int(sp.x), int(sp.y))
        self.player.velocity = pygame.Vector2(0, 0)
        self.player.health = C.PLAYER_MAX_HEALTH
        self.player.on_ground = False
        self.player.dead = False
        self.player.state = "idle"
        self.player.rolling_timer = 0.0
        self.player.jump_buffer_timer = 0.0
        self.player.coyote_timer = 0.0
        self.player.run_buildup = 0.0
        self.player.invuln_timer = 1.5
        self.player.handle(InputSnapshot())
        self.camera.snap_to(pygame.Vector2(sp.x + 14, sp.y + 22))

    def draw(self, surf: pygame.Surface) -> None:
        self.renderer.draw_frame(
            self.level, self.camera,
            [self.player] + self.level.entities,
            particles=self.particles,
            shake=(self._shake_x, self._shake_y),
        )
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
        aape_display = "COMPLETE!" if r["aape_complete"] else f"{len(r['aape'])} / 4"
        lines = [
            (f"Time:     {mins:02d}:{secs:02d}", (200, 230, 200), r.get("new_time", False)),
            (f"Bananas:  {r['bananas']} / {r['total_bananas']}", (255, 220, 70), r.get("new_bananas", False)),
            (f"AAPE:     {aape_display}", (250, 200, 60) if r["aape_complete"] else (160, 130, 60), False),
        ]

        font_nr = pygame.font.SysFont("arial", 16, bold=True)
        for i, (line, col, is_new) in enumerate(lines):
            txt = self.font_med.render(line, True, col)
            rect = txt.get_rect(center=(w // 2, 180 + i * 52))
            surf.blit(txt, rect)
            if is_new:
                badge = font_nr.render("★ NEW BEST", True, (255, 230, 80))
                surf.blit(badge, badge.get_rect(midleft=(rect.right + 12, rect.centery)))

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
