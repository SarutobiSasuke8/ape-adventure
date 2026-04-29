"""Snapper — patrols back and forth, defeated by roll or stomp."""
from __future__ import annotations

import math

import pygame

from ape_adventure.core import constants as C
from ape_adventure.core.physics import move_and_collide
from ape_adventure.entities.enemies.enemy import Enemy
from ape_adventure.render import palette as P


class Snapper(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=32, h=28, hp=1)
        self.patrol_speed = 65.0
        self.velocity.x = self.patrol_speed * self.facing
        self.anim_t = 0.0
        self.death_timer = 0.35   # seconds of death squish before removal
        self._dying = False

    # ------------------------------------------------------------------

    def update(self, dt: float, world) -> None:
        if self._dying:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.alive = False
            return

        tg = world.tile_grid
        ts = tg.tile_size

        # Edge detection: peek at the tile ahead-and-below the leading foot
        if self.on_ground:
            lead_x = self.pos.x + (self.rect.width + 2 if self.facing > 0 else -2)
            floor_row = int((self.pos.y + self.rect.height + 4) // ts)
            lead_col = int(lead_x // ts)
            if tg.get(lead_col, floor_row) == 0:
                self.facing = -self.facing

        self.velocity.x = self.patrol_speed * self.facing

        # Gravity
        if not self.on_ground:
            self.velocity.y = min(self.velocity.y + C.GRAVITY * dt, C.TERMINAL_VELOCITY)

        self.pos, self.velocity, collisions = move_and_collide(
            self.pos, self.rect, self.velocity, tg, dt
        )
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.on_ground = collisions["bottom"]

        if collisions["left"] or collisions["right"]:
            self.facing = -self.facing

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
        f = self.facing
        W = self.rect.width

        if self._dying:
            # Squish on death
            squish = pygame.Rect(sx, sy + 18, W, 10)
            pygame.draw.rect(surf, P.SAURIAN_GREEN, squish, border_radius=4)
            return

        lo = int(math.sin(self.anim_t * 7.5) * 4)

        # Tail
        tx = sx if f > 0 else sx + W
        tail = [
            (tx, sy + 12),
            (tx - 10 * f, sy + 18),
            (tx, sy + 22),
        ]
        pygame.draw.polygon(surf, P.SAURIAN_GREEN, tail)

        # Body
        body = pygame.Rect(sx + 2, sy + 8, W - 6, 18)
        pygame.draw.rect(surf, P.SAURIAN_GREEN, body, border_radius=5)
        pygame.draw.rect(surf, (70, 115, 42), body.inflate(-6, -6), border_radius=3)

        # Head
        hx = sx + W - 15 if f > 0 else sx
        pygame.draw.ellipse(surf, P.SAURIAN_GREEN, pygame.Rect(hx, sy + 2, 18, 16))

        # Snout
        snout_x = sx + W - 3 if f > 0 else sx - 6
        pygame.draw.rect(surf, P.SAURIAN_BELLY, pygame.Rect(snout_x, sy + 8, 8, 6), border_radius=2)

        # Eye
        ex = sx + W - 8 if f > 0 else sx + 6
        pygame.draw.circle(surf, (200, 40, 30), (ex, sy + 6), 4)
        pygame.draw.circle(surf, (255, 220, 0), (ex, sy + 6), 2)

        # Legs
        for i, off in enumerate([5, 18]):
            leg_lo = lo if i == 0 else -lo
            pygame.draw.rect(surf, P.SAURIAN_GREEN,
                             pygame.Rect(sx + off, sy + 22 + leg_lo, 7, 8), border_radius=2)
