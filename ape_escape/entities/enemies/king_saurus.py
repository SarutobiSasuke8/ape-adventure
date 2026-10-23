"""King Saurus, the World 1 boss. Charge, crash, punish: three hits to defeat.

Pattern (one cycle):

  telegraph  -> stamps in place, facing the player (harmful)
  charge     -> runs at the player until he hits a wall (harmful)
  dazed      -> stunned after the crash; safe to touch, stomp to damage him
  hurt       -> after a stomp he slides back towards the arena centre (safe)

Each hit raises the phase: faster charges, shorter telegraph and daze, and
from phase 2 a hop part-way through the charge. Rolling into him never
hurts him; only a stomp while he is dazed counts.

Visuals are PLACEHOLDER procedural vector art (see docs/placeholder-art.md).
"""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.core.physics import move_and_collide
from ape_escape.entities.enemies.enemy import Enemy
from ape_escape.render import palette as P

# Per-phase tuning: index 0 = phase 1.
_CHARGE_SPEED = (210.0, 270.0, 330.0)
_TELEGRAPH_TIME = (0.90, 0.70, 0.50)
_DAZE_TIME = (1.80, 1.40, 1.05)
_HOP_IMPULSE = -420.0
_HOP_AFTER_PX = 96.0      # distance into a charge before the phase 2+ hop
_HURT_TIME = 0.80
_HURT_SLIDE_SPEED = 200.0
_DEFEAT_TIME = 1.20


class KingSaurus(Enemy):
    STOMP_BOUNCE = -520.0

    def __init__(self, x: float, y: float) -> None:
        # 56 px tall so a two-tile (64 px) ledge clears his head.
        super().__init__(x, y, w=72, h=56, hp=3)
        self.max_hp = 3
        self.phase = 1  # 1..3, rises with each hit
        self.state = "telegraph"
        self.state_timer = 1.2  # a longer first telegraph so the player can read it
        self.facing = -1
        self._charge_start_x = 0.0
        self._hopped = False
        self.anim_t = 0.0
        self.target_x: float | None = None  # player centre x, set by LevelState
        self.crashed = False  # set on a wall crash; LevelState reads and clears it

    # ------------------------------------------------------------------
    # Contact contract
    # ------------------------------------------------------------------

    @property
    def harmful(self) -> bool:
        return self.state in ("telegraph", "charge") and not self._dying

    @property
    def vulnerable(self) -> bool:
        return self.state == "dazed" and not self._dying

    def on_stomp(self) -> bool:
        if not self.vulnerable:
            return False  # bounce off harmlessly
        self.hp -= 1
        if self.hp <= 0:
            self.die()
        else:
            self.phase = min(3, self.max_hp - self.hp + 1)
            self._enter("hurt", _HURT_TIME)
        return True

    def on_roll(self) -> bool:
        return False  # too big to bowl over

    def die(self) -> None:
        self._dying = True
        self.state = "defeated"
        self.state_timer = _DEFEAT_TIME
        self.velocity = pygame.Vector2(0, self.velocity.y)

    # ------------------------------------------------------------------

    def _enter(self, state: str, timer: float) -> None:
        self.state = state
        self.state_timer = timer

    def _face_target(self) -> None:
        if self.target_x is not None:
            self.facing = 1 if self.target_x > self.rect.centerx else -1

    def update(self, dt: float, world) -> None:
        self.anim_t += dt
        tg = world.tile_grid
        i = self.phase - 1

        if self.state == "defeated":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.alive = False
            self.velocity.x = 0.0
        elif self.state == "telegraph":
            self._face_target()
            self.velocity.x = 0.0
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._enter("charge", 0.0)
                self._charge_start_x = self.pos.x
                self._hopped = False
        elif self.state == "charge":
            self.velocity.x = _CHARGE_SPEED[i] * self.facing
            travelled = abs(self.pos.x - self._charge_start_x)
            if self.phase >= 2 and not self._hopped and self.on_ground and travelled >= _HOP_AFTER_PX:
                self.velocity.y = _HOP_IMPULSE
                self.on_ground = False
                self._hopped = True
        elif self.state == "dazed":
            self.velocity.x = 0.0
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._face_target()
                self._enter("telegraph", _TELEGRAPH_TIME[i])
        elif self.state == "hurt":
            # Slide back towards the arena centre, away from the wall he hit.
            centre = world.bounds.width / 2.0
            self.velocity.x = _HURT_SLIDE_SPEED * (1 if self.rect.centerx < centre else -1)
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._face_target()
                self._enter("telegraph", _TELEGRAPH_TIME[i])

        if not self.on_ground:
            self.velocity.y = min(self.velocity.y + C.GRAVITY * dt, C.TERMINAL_VELOCITY)

        self.pos, self.velocity, collisions = move_and_collide(
            self.pos, self.rect, self.velocity, tg, dt
        )
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.on_ground = collisions["bottom"]

        if self.state == "charge" and (collisions["left"] or collisions["right"]):
            self._enter("dazed", _DAZE_TIME[i])
            self.crashed = True  # read once by LevelState for shake/SFX
        elif self.state == "hurt" and (collisions["left"] or collisions["right"]):
            self.state_timer = 0.0

    # ------------------------------------------------------------------
    # Draw (PLACEHOLDER procedural art)
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        sp = camera.world_to_screen(self.pos)
        sx, sy = int(sp.x), int(sp.y)
        W, H = self.rect.width, self.rect.height
        f = self.facing

        if self.state == "defeated":
            # Sink and flash out.
            if int(self.state_timer * 12) % 2 == 0:
                return
            sink = int((1.0 - self.state_timer / _DEFEAT_TIME) * 24)
            body = pygame.Rect(sx, sy + sink, W, H - sink)
            pygame.draw.rect(surf, P.SAURIAN_GREEN, body, border_radius=12)
            return

        # Phase colour shift: green -> olive -> angry red.
        tint = (P.SAURIAN_GREEN, (130, 120, 50), P.SAURIAN_RED)[self.phase - 1]
        if self.state == "hurt" and int(self.anim_t * 14) % 2 == 0:
            tint = (240, 240, 240)

        bob = 0
        if self.state == "telegraph":
            bob = int(abs(math.sin(self.anim_t * 14.0)) * 4)
        elif self.state == "charge":
            bob = int(math.sin(self.anim_t * 20.0) * 2)

        # Tail
        tx = sx if f > 0 else sx + W
        pygame.draw.polygon(surf, tint, [(tx, sy + 22), (tx - 22 * f, sy + 36), (tx, sy + 46)])

        # Body + belly
        body = pygame.Rect(sx + 4, sy + 10 + bob, W - 8, H - 18)
        pygame.draw.rect(surf, tint, body, border_radius=12)
        pygame.draw.rect(surf, P.SAURIAN_BELLY, body.inflate(-22, -16).move(4 * f, 4), border_radius=8)

        # Legs
        for off in (10, W - 24):
            pygame.draw.rect(surf, tint, pygame.Rect(sx + off, sy + H - 12, 14, 12), border_radius=3)

        # Head
        hx = sx + W - 30 if f > 0 else sx + 2
        head = pygame.Rect(hx, sy + 2 + bob, 28, 24)
        pygame.draw.ellipse(surf, tint, head)
        snout_x = head.right - 4 if f > 0 else head.left - 8
        pygame.draw.rect(surf, P.SAURIAN_BELLY, pygame.Rect(snout_x, head.y + 12, 12, 8), border_radius=3)

        # Eye: spirals when dazed
        ex = head.centerx + 5 * f
        ey = head.y + 9
        if self.state == "dazed":
            for k in range(3):
                a = self.anim_t * 6 + k * 2.1
                pygame.draw.circle(surf, P.CANOPY_GOLD,
                                   (int(sx + W / 2 + math.cos(a) * 18), int(sy - 8 + math.sin(a) * 5)), 3)
            pygame.draw.line(surf, (20, 10, 6), (ex - 3, ey - 3), (ex + 3, ey + 3), 2)
            pygame.draw.line(surf, (20, 10, 6), (ex - 3, ey + 3), (ex + 3, ey - 3), 2)
        else:
            pygame.draw.circle(surf, (200, 40, 30), (ex, ey), 4)
            pygame.draw.circle(surf, (255, 220, 0), (ex, ey), 2)

        # Crown
        cx = head.centerx
        cy = head.y - 2
        crown = [(cx - 10, cy), (cx - 10, cy - 9), (cx - 5, cy - 4), (cx, cy - 11),
                 (cx + 5, cy - 4), (cx + 10, cy - 9), (cx + 10, cy)]
        pygame.draw.polygon(surf, P.CANOPY_GOLD, crown)

        # HP pips above the head
        for k in range(self.max_hp):
            col = P.HEART_FULL if k < self.hp else P.HEART_EMPTY
            pygame.draw.circle(surf, col, (sx + W // 2 - 12 + k * 12, sy - 18), 4)
