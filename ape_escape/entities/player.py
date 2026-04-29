"""Bongo — the player character."""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot
from ape_escape.core.physics import move_and_collide
from ape_escape.entities.entity import Entity
from ape_escape.render import palette as P


class Player(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=28, h=44)
        self.health = C.PLAYER_MAX_HEALTH
        self.state = "idle"  # idle | walk | run | jump | fall | roll | hurt

        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.invuln_timer = 0.0
        self.rolling_timer = 0.0
        self.run_buildup = 0.0   # seconds of sustained directional input
        self.anim_t = 0.0
        self.dead = False

        self._snap = InputSnapshot()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle(self, snapshot: InputSnapshot) -> None:
        self._snap = snapshot

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, world) -> None:
        if self.dead:
            return

        sn = self._snap
        tile_grid = world.tile_grid

        self.anim_t += dt

        # --- Timers ---
        self.coyote_timer = max(0.0, self.coyote_timer - dt)
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        self.invuln_timer = max(0.0, self.invuln_timer - dt)

        # --- Roll ---
        if self.rolling_timer > 0:
            self.rolling_timer = max(0.0, self.rolling_timer - dt)
        elif sn.roll and self.on_ground and self.state != "hurt":
            self.rolling_timer = C.PLAYER_ROLL_DURATION
            self.velocity.x = C.PLAYER_ROLL_SPEED * self.facing

        # --- Buffer jump press ---
        if sn.jump:
            self.jump_buffer_timer = C.PLAYER_JUMP_BUFFER

        # --- Horizontal movement (locked while rolling) ---
        if self.rolling_timer <= 0:
            if sn.move_x != 0:
                self.facing = int(sn.move_x)
                self.run_buildup += dt
                is_running = sn.run or self.run_buildup >= 0.4
                target_spd = C.PLAYER_RUN_SPEED if is_running else C.PLAYER_WALK_SPEED
                accel = 14.0  # responsiveness multiplier
                self.velocity.x += (target_spd * sn.move_x - self.velocity.x) * min(1.0, accel * dt)
            else:
                self.run_buildup = 0.0
                friction = 18.0
                self.velocity.x *= max(0.0, 1.0 - friction * dt)
                if abs(self.velocity.x) < 4.0:
                    self.velocity.x = 0.0

        # --- Jump ---
        can_jump = self.on_ground or self.coyote_timer > 0
        if self.jump_buffer_timer > 0 and can_jump:
            self.velocity.y = C.PLAYER_JUMP_IMPULSE
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0

        # --- Variable jump height (release early for lower arc) ---
        if not sn.jump_held and self.velocity.y < 0:
            self.velocity.y += C.GRAVITY * C.PLAYER_VARIABLE_JUMP_FACTOR * dt

        # --- Gravity ---
        if not self.on_ground:
            self.velocity.y = min(
                self.velocity.y + C.GRAVITY * dt,
                C.TERMINAL_VELOCITY,
            )

        # --- Physics ---
        was_on_ground = self.on_ground
        self.pos, self.velocity, collisions = move_and_collide(
            self.pos, self.rect, self.velocity, tile_grid, dt
        )
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.on_ground = collisions["bottom"]

        # Coyote time starts when stepping off a ledge (not from a jump)
        if was_on_ground and not self.on_ground and self.velocity.y >= 0:
            self.coyote_timer = C.PLAYER_COYOTE_TIME

        if collisions["top"]:
            self.velocity.y = 0.0

        # --- State machine ---
        if self.rolling_timer > 0:
            self.state = "roll"
        elif not self.on_ground:
            self.state = "jump" if self.velocity.y < 0 else "fall"
        elif abs(self.velocity.x) >= C.PLAYER_RUN_SPEED * 0.6:
            self.state = "run"
        elif abs(self.velocity.x) >= 5.0:
            self.state = "walk"
        else:
            self.state = "idle"

    # ------------------------------------------------------------------
    # Draw (placeholder vector art — replace with sprite sheet later)
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface, camera) -> None:
        sp = camera.world_to_screen(self.pos)
        sx, sy = int(sp.x), int(sp.y)

        # Flicker when invulnerable
        if self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2 == 0:
            return

        rolling = self.rolling_timer > 0
        bw, bh = (40, 24) if rolling else (28, 36)
        by = sy + (44 - bh)  # anchor to feet

        body = pygame.Rect(sx, by, bw, bh)

        # Shadow
        pygame.draw.ellipse(surf, (10, 30, 15, 80), pygame.Rect(sx - 4, sy + 41, bw + 8, 8))

        # Body
        pygame.draw.rect(surf, P.BONGO_FUR, body, border_radius=7)
        pygame.draw.rect(surf, P.BONGO_FUR_LIGHT, body.inflate(-6, -8), border_radius=5)

        if not rolling:
            # Legs
            t = self.anim_t
            if self.state in ("walk", "run"):
                spd = 12.0 if self.state == "run" else 7.0
                lo = int(math.sin(t * spd) * 6)
            else:
                lo = 0
            leg_y = sy + 36
            pygame.draw.rect(surf, P.BONGO_FUR, pygame.Rect(sx + 4, leg_y + lo, 9, 12), border_radius=3)
            pygame.draw.rect(surf, P.BONGO_FUR, pygame.Rect(sx + 15, leg_y - lo, 9, 12), border_radius=3)

            # Head
            hcx = sx + 14
            hcy = sy + 4
            pygame.draw.circle(surf, P.BONGO_FUR, (hcx, hcy), 15)
            # Face patch
            pygame.draw.ellipse(surf, P.BONGO_FUR_LIGHT, pygame.Rect(hcx - 9, hcy - 6, 18, 14))
            # Eye (facing direction)
            ex = hcx + (5 if self.facing > 0 else -5)
            pygame.draw.circle(surf, (18, 10, 6), (ex, hcy - 1), 3)
            pygame.draw.circle(surf, (255, 255, 255), (ex + self.facing, hcy - 2), 1)

            # Idle breathing bob
            if self.state == "idle":
                bob = int(math.sin(self.anim_t * 2.5) * 1.5)
                pygame.draw.rect(surf, P.BONGO_FUR_LIGHT,
                                 pygame.Rect(sx + 6, by + 4 + bob, bw - 12, 6), border_radius=3)
