"""Hopper — small, fast lizard that hops along platforms."""
from __future__ import annotations

import math

import pygame

from ape_adventure.core import constants as C
from ape_adventure.core.physics import move_and_collide
from ape_adventure.entities.enemies.enemy import Enemy
from ape_adventure.render import palette as P


class Hopper(Enemy):
    """Patrols by hopping in its facing direction at a fixed cadence.

    Defeated by stomp (landing on top while falling) or by a roll attack.
    Cannot be walked into safely — contact from the side damages the player.
    """

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=26, h=24, hp=1)
        self.hop_impulse:  float = -340.0   # vertical kick on each hop
        self.hop_speed:    float = 105.0    # horizontal speed while airborne
        self.hop_cooldown: float = 0.75     # seconds between hops (grounded rest)
        self._cooldown_timer: float = 0.2   # short initial delay so spawn looks natural
        self._dying:       bool  = False
        self.death_timer:  float = 0.28
        self.anim_t:       float = 0.0

    # ------------------------------------------------------------------

    def update(self, dt: float, world) -> None:
        if self._dying:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.alive = False
            return

        tg = world.tile_grid
        ts = tg.tile_size

        # Gravity when airborne
        if not self.on_ground:
            self.velocity.y = min(self.velocity.y + C.GRAVITY * dt, C.TERMINAL_VELOCITY)

        if self.on_ground:
            # Friction on landing
            self.velocity.x *= max(0.0, 1.0 - 18.0 * dt)

            # Count down to next hop
            self._cooldown_timer -= dt
            if self._cooldown_timer <= 0:
                # Edge detection: check tile below the leading foot
                lead_x    = self.pos.x + (self.rect.width + 4 if self.facing > 0 else -4)
                floor_row = int((self.pos.y + self.rect.height + 6) // ts)
                lead_col  = int(lead_x // ts)
                if tg.get(lead_col, floor_row) == 0:
                    self.facing = -self.facing  # reverse before hopping into void

                # Hop!
                self.velocity.y = self.hop_impulse
                self.velocity.x = self.hop_speed * self.facing
                self._cooldown_timer = self.hop_cooldown

        self.pos, self.velocity, collisions = move_and_collide(
            self.pos, self.rect, self.velocity, tg, dt
        )
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.on_ground = collisions["bottom"]

        # Bounce off walls mid-air
        if collisions["left"] or collisions["right"]:
            self.facing = -self.facing
            self.velocity.x = self.hop_speed * self.facing * 0.6

        if collisions["bottom"]:
            self.velocity.x = 0.0  # let friction handle deceleration on ground

        self.anim_t += dt

    def die(self) -> None:
        self._dying = True
        self.velocity = pygame.Vector2(0, 0)

    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface, camera) -> None:
        if not self.alive:
            return

        sp = camera.world_to_screen(self.pos)
        sx, sy = int(sp.x), int(sp.y)
        f  = self.facing
        W  = self.rect.width
        H  = self.rect.height

        if self._dying:
            squish = pygame.Rect(sx, sy + H - 8, W, 8)
            pygame.draw.rect(surf, P.SAURIAN_GREEN, squish, border_radius=3)
            return

        # Squash-and-stretch: flatten on ground, elongate during jump apex
        if self.on_ground:
            # Rhythmic breathing squash while waiting for next hop
            sq = int(math.sin(self.anim_t * 8.0) * 1.5)
        else:
            # Stretch upward on ascent, compress on descent
            sq = -3 if self.velocity.y < -80 else 1

        body_h  = H - 10 - sq
        body_y  = sy + 4 + sq // 2

        # --- Big back legs (signature silhouette) ---
        back_x = sx if f > 0 else sx + W - 9
        pygame.draw.rect(
            surf, P.SAURIAN_GREEN,
            pygame.Rect(back_x, sy + H - 16 + sq, 9, 16 - sq),
            border_radius=4,
        )
        # Foot pad
        pygame.draw.ellipse(
            surf, (60, 100, 40),
            pygame.Rect(back_x - 2, sy + H - 5, 13, 5),
        )

        # --- Front stub legs ---
        front_x = sx + W - 8 if f > 0 else sx
        pygame.draw.rect(
            surf, P.SAURIAN_GREEN,
            pygame.Rect(front_x, sy + H - 9, 8, 9),
            border_radius=2,
        )

        # --- Body ---
        body = pygame.Rect(sx, body_y, W, body_h)
        pygame.draw.rect(surf, P.SAURIAN_GREEN, body, border_radius=7)
        # Belly stripe
        belly = body.inflate(-6, -6)
        belly.y += 2
        pygame.draw.rect(surf, P.SAURIAN_BELLY, belly, border_radius=4)

        # --- Head (small, rounded) ---
        hx = sx + W - 13 if f > 0 else sx - 2
        pygame.draw.ellipse(surf, P.SAURIAN_GREEN, pygame.Rect(hx, sy, 14, 11))

        # --- Beady eye ---
        ex = sx + W - 6 if f > 0 else sx + 5
        pygame.draw.circle(surf, (210, 50, 30), (ex, sy + 4), 3)
        pygame.draw.circle(surf, (255, 235, 60), (ex, sy + 4), 1)

        # --- Tiny snout ---
        snout_x = sx + W - 2 if f > 0 else sx - 4
        pygame.draw.rect(
            surf, P.SAURIAN_BELLY,
            pygame.Rect(snout_x, sy + 5, 5, 4),
            border_radius=1,
        )
