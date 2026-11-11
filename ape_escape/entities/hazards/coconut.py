"""Coconut: a falling hazard shaken loose by King Saurus's roar (final phase).

Life cycle:

  warn   -> hangs in the canopy, shaking, while a shadow grows on the ground
            below it (harmless). This is the tell: the shadow marks exactly
            where it will land.
  fall   -> drops straight down under gravity (harmful on contact)
  smash  -> bursts on the ground or on Bongo, then disappears (harmless)

A coconut only ever moves vertically, so stepping out of its shadow during
the warning dodges it. Stomps and rolls do nothing to it.

Visuals are PLACEHOLDER procedural art (see docs/placeholder-art.md).
"""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.entities.entity import Entity
from ape_escape.render import palette as P

COCONUT_SIZE = 20
WARN_TIME = 0.90
SMASH_TIME = 0.25
CANOPY_Y = 104.0  # world y (top) where coconuts hang: in view, clear of the HUD

_SHELL = (110, 70, 40)
_SHELL_DARK = (70, 42, 24)
_FLESH = (240, 236, 220)


class Coconut(Entity):
    def __init__(self, centre_x: float, warn_time: float = WARN_TIME, top_y: float = CANOPY_Y) -> None:
        s = COCONUT_SIZE
        super().__init__(centre_x - s / 2, top_y, w=s, h=s)
        self.state = "warn"
        self.timer = warn_time
        self.warn_time = max(0.001, warn_time)
        self.ground_y: float | None = None  # surface below, found on first update
        self.t = 0.0

    @property
    def harmful(self) -> bool:
        return self.state == "fall"

    def smash(self) -> None:
        if self.state != "smash":
            self.state = "smash"
            self.timer = SMASH_TIME
            self.velocity.update(0, 0)

    def find_ground(self, tg) -> float:
        """World y of the first solid surface straight below."""
        col = int(self.rect.centerx // tg.tile_size)
        row = max(0, int(self.rect.bottom // tg.tile_size))
        while row < tg.height:
            if tg.get(col, row):
                return float(row * tg.tile_size)
            row += 1
        return float(tg.height * tg.tile_size + 200)  # bottomless: falls off the world

    def update(self, dt: float, world) -> None:
        self.t += dt
        tg = world.tile_grid
        if self.ground_y is None:
            self.ground_y = self.find_ground(tg)

        if self.state == "warn":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "fall"
        elif self.state == "fall":
            self.velocity.y = min(self.velocity.y + C.GRAVITY * dt, C.TERMINAL_VELOCITY)
            self.pos.y += self.velocity.y * dt
            if self.pos.y + self.rect.height >= self.ground_y:
                self.pos.y = self.ground_y - self.rect.height
                self.smash()
        elif self.state == "smash":
            self.timer -= dt
            if self.timer <= 0:
                self.alive = False
        if self.pos.y > world.bounds.height + 100:
            self.alive = False
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

    # ------------------------------------------------------------------
    # Draw (PLACEHOLDER procedural art)
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        r = COCONUT_SIZE // 2
        cx = self.rect.centerx

        # Shadow tell on the ground: grows and darkens as the drop nears.
        if self.ground_y is not None and self.state in ("warn", "fall"):
            if self.state == "warn":
                k = 1.0 - self.timer / self.warn_time
            else:
                span = max(1.0, self.ground_y - CANOPY_Y)
                k = 1.0 + min(1.0, (self.pos.y - CANOPY_Y) / span) * 0.4
            w = int(10 + 22 * min(1.4, k))
            gp = camera.world_to_screen(pygame.Vector2(cx, self.ground_y))
            shadow = pygame.Surface((w * 2, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (10, 8, 6, int(60 + 110 * min(1.0, k))), shadow.get_rect())
            surf.blit(shadow, (int(gp.x) - w, int(gp.y) - 5))

        sp = camera.world_to_screen(pygame.Vector2(cx, self.rect.centery))
        x, y = int(sp.x), int(sp.y)
        if self.state == "warn":
            x += int(math.sin(self.t * 40.0) * 2)  # shaking loose
            # Stalk up into the canopy
            pygame.draw.line(surf, P.JUNGLE_MID, (x, y - r - 14), (x, y - r), 3)
        if self.state == "smash":
            k = 1.0 - self.timer / SMASH_TIME
            for a in (-2.4, -1.6, -0.8, -0.2):
                dx = int(math.cos(a) * (6 + 14 * k))
                dy = int(math.sin(a) * (4 + 8 * k))
                pygame.draw.circle(surf, _SHELL if a < -1.2 else _FLESH, (x + dx, y + dy + r // 2), 4)
            return
        pygame.draw.circle(surf, _SHELL, (x, y), r)
        pygame.draw.circle(surf, _SHELL_DARK, (x, y), r, 2)
        for ex in (-4, 0, 4):
            pygame.draw.circle(surf, _SHELL_DARK, (x + ex, y - 4), 2)
