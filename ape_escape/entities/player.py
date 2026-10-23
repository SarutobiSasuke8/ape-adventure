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
        super().__init__(x, y, w=28, h=C.PLAYER_STAND_HEIGHT)
        self.health = C.PLAYER_MAX_HEALTH
        self.state = "idle"  # idle | walk | run | jump | fall | roll | crawl | swing | hurt

        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.roll_buffer_timer = 0.0
        self.invuln_timer = 0.0
        self.rolling_timer = 0.0
        self.run_buildup = 0.0   # seconds of sustained directional input
        self.anim_t = 0.0
        self.dead = False
        self.crouched = False    # short hitbox: rolling, or crawling under a low ceiling

        # Vine swing (vine is None when not swinging)
        self.vine = None
        self.swing_radius = 0.0
        self.swing_theta = 0.0
        self.swing_omega = 0.0
        self._last_vine = None
        self._regrab_timer = 0.0

        self._snap = InputSnapshot()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle(self, snapshot: InputSnapshot) -> None:
        self._snap = snapshot

    # ------------------------------------------------------------------
    # Posture (stand / crouch hitbox)
    # ------------------------------------------------------------------

    def _set_crouched(self, crouched: bool, tile_grid) -> bool:
        """Switch hitbox height, keeping the feet in place. False if blocked."""
        if crouched == self.crouched:
            return True
        delta = C.PLAYER_STAND_HEIGHT - C.PLAYER_CROUCH_HEIGHT
        if crouched:
            self.pos.y += delta
            self.rect.height = C.PLAYER_CROUCH_HEIGHT
        else:
            standing = pygame.Rect(self.rect.x, self.rect.bottom - C.PLAYER_STAND_HEIGHT,
                                   self.rect.width, C.PLAYER_STAND_HEIGHT)
            if tile_grid is not None and any(
                standing.colliderect(t) for t in tile_grid.solid_tiles_near(standing)
            ):
                return False
            self.pos.y -= delta
            self.rect.height = C.PLAYER_STAND_HEIGHT
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.crouched = crouched
        return True

    def reset_posture(self) -> None:
        """Stand up and drop any vine (respawn). The caller sets the position."""
        self.crouched = False
        self.rect.height = C.PLAYER_STAND_HEIGHT
        if self.vine is not None:
            self.detach_vine()
        self._last_vine = None
        self._regrab_timer = 0.0

    # ------------------------------------------------------------------
    # Vine swing
    # ------------------------------------------------------------------

    def grip_point(self) -> pygame.Vector2:
        return pygame.Vector2(self.pos.x + self.rect.width / 2.0, self.pos.y + C.VINE_GRIP_OFFSET)

    def can_grab(self, vine) -> bool:
        if self.dead or self.vine is not None or self.on_ground or self.crouched:
            return False
        return not (vine is self._last_vine and self._regrab_timer > 0)

    def attach_to_vine(self, vine, radius: float) -> None:
        grip = self.grip_point()
        d = grip - vine.anchor
        r = max(vine.length * 0.35, min(vine.length, radius))
        theta = math.atan2(d.x, d.y)
        tangent = pygame.Vector2(math.cos(theta), -math.sin(theta))
        self.vine = vine
        self.swing_radius = r
        self.swing_theta = theta
        self.swing_omega = self.velocity.dot(tangent) / r
        self.rolling_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        vine.held = True
        self._place_on_vine()
        self.state = "swing"

    def detach_vine(self) -> None:
        v = self.vine
        if v is None:
            return
        v.held = False
        v.theta = self.swing_theta
        v.omega = self.swing_omega * self.swing_radius / v.length
        self._last_vine = v
        self._regrab_timer = C.VINE_REGRAB_COOLDOWN
        self.vine = None

    def _swing_velocity(self) -> pygame.Vector2:
        th = self.swing_theta
        return pygame.Vector2(math.cos(th), -math.sin(th)) * (self.swing_radius * self.swing_omega)

    def _place_on_vine(self) -> None:
        v = self.vine
        th = self.swing_theta
        grip = v.anchor + pygame.Vector2(math.sin(th), math.cos(th)) * self.swing_radius
        self.pos = pygame.Vector2(grip.x - self.rect.width / 2.0, grip.y - C.VINE_GRIP_OFFSET)
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        v.theta = th
        v.hold_radius = self.swing_radius

    def _update_swing(self, dt: float, sn: InputSnapshot, tile_grid) -> None:
        if sn.jump:
            vel = self._swing_velocity()
            vel.y = max(-720.0, min(vel.y, 0.0) + C.VINE_RELEASE_BOOST)
            self.detach_vine()
            self.velocity = vel
            self.jump_buffer_timer = 0.0
            self.on_ground = False
            self.state = "jump"
            return

        r = self.swing_radius
        alpha = -(C.GRAVITY / r) * math.sin(self.swing_theta)
        alpha += sn.move_x * C.VINE_PUMP_ACCEL / r
        self.swing_omega += alpha * dt
        self.swing_omega *= max(0.0, 1.0 - C.VINE_DAMPING * dt)
        prev_theta = self.swing_theta
        self.swing_theta += self.swing_omega * dt
        if abs(self.swing_theta) > C.VINE_MAX_ANGLE:
            self.swing_theta = math.copysign(C.VINE_MAX_ANGLE, self.swing_theta)
            self.swing_omega = 0.0
        self._place_on_vine()
        # Never swing into scenery: stop at the last clear angle.
        if tile_grid is not None and any(
            self.rect.colliderect(t) for t in tile_grid.solid_tiles_near(self.rect)
        ):
            self.swing_theta = prev_theta
            self.swing_omega = 0.0
            self._place_on_vine()

        self.velocity = self._swing_velocity()
        if abs(self.swing_omega) > 0.05:
            self.facing = 1 if self.swing_omega > 0 else -1
        self.on_ground = False
        self.state = "swing"

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
        self.roll_buffer_timer = max(0.0, self.roll_buffer_timer - dt)
        self.invuln_timer = max(0.0, self.invuln_timer - dt)
        self._regrab_timer = max(0.0, self._regrab_timer - dt)

        # --- Vine swing replaces normal movement while holding on ---
        if self.vine is not None:
            self._update_swing(dt, sn, tile_grid)
            return

        # --- Roll (drops to the short hitbox, so it fits under low logs) ---
        # Buffered and coyote-timed like the jump: ground contact flickers
        # frame to frame, so an edge-triggered press alone was often dropped.
        if sn.roll:
            self.roll_buffer_timer = C.PLAYER_ROLL_BUFFER
        grounded = self.on_ground or self.coyote_timer > 0
        if self.rolling_timer > 0:
            self.rolling_timer = max(0.0, self.rolling_timer - dt)
        elif self.roll_buffer_timer > 0 and grounded and self.state != "hurt":
            self.roll_buffer_timer = 0.0
            self.rolling_timer = C.PLAYER_ROLL_DURATION
            self.velocity.x = C.PLAYER_ROLL_SPEED * self.facing
            self._set_crouched(True, tile_grid)

        # Stand up when the roll ends, unless a ceiling is in the way (crawl).
        if self.rolling_timer <= 0 and self.crouched:
            self._set_crouched(False, tile_grid)
        crawling = self.crouched and self.rolling_timer <= 0

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
                if crawling:
                    target_spd = C.PLAYER_CRAWL_SPEED
                accel = 14.0  # responsiveness multiplier
                self.velocity.x += (target_spd * sn.move_x - self.velocity.x) * min(1.0, accel * dt)
            else:
                self.run_buildup = 0.0
                friction = 18.0
                self.velocity.x *= max(0.0, 1.0 - friction * dt)
                if abs(self.velocity.x) < 4.0:
                    self.velocity.x = 0.0

        # --- Jump (not while crawling under a low ceiling) ---
        can_jump = (self.on_ground or self.coyote_timer > 0) and not crawling
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
        elif crawling:
            self.state = "crawl"
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

        low = self.rolling_timer > 0 or self.crouched
        bw, bh = (40, 24) if low else (28, 36)
        feet = sy + self.rect.height
        by = feet - bh  # anchor to feet
        bx = sx - (bw - self.rect.width) // 2 if low else sx

        body = pygame.Rect(bx, by, bw, bh)

        # Shadow (none while swinging)
        if self.vine is None:
            pygame.draw.ellipse(surf, (10, 30, 15, 80), pygame.Rect(bx - 4, feet - 3, bw + 8, 8))
        else:
            # Arms up to the vine grip
            gx, gy = sx + self.rect.width // 2, sy + C.VINE_GRIP_OFFSET
            pygame.draw.line(surf, P.BONGO_FUR, (sx + 4, sy + 16), (gx, gy), 5)
            pygame.draw.line(surf, P.BONGO_FUR, (sx + self.rect.width - 4, sy + 16), (gx, gy), 5)

        # Body
        pygame.draw.rect(surf, P.BONGO_FUR, body, border_radius=7)
        pygame.draw.rect(surf, P.BONGO_FUR_LIGHT, body.inflate(-6, -8), border_radius=5)

        if not low:
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
        elif self.crouched and self.rolling_timer <= 0:
            # Crawling: keep the eye visible at the leading edge
            ex = body.right - 8 if self.facing > 0 else body.left + 8
            pygame.draw.circle(surf, (18, 10, 6), (ex, by + 8), 3)
