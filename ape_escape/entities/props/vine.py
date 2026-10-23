"""Vine: a swing rope hanging from an anchor. Grab it in mid-air, jump to let go.

The vine is a simple pendulum. While the player holds it, the player owns
the swing (see ``Player.attach_to_vine``) and the vine just mirrors the
player's angle. Once released it swings on by itself and settles.

Visuals are PLACEHOLDER procedural vector art (see docs/placeholder-art.md).
"""
from __future__ import annotations

import math

import pygame

from ape_escape.core import constants as C
from ape_escape.entities.entity import Entity

GRAB_RADIUS = 20.0        # px from the vine line to the player's grip point
GRAB_MIN_FRACTION = 0.35  # grip must be at least this far down the vine


class Vine(Entity):
    def __init__(self, anchor_x: float, anchor_y: float, length: float) -> None:
        super().__init__(anchor_x - 6, anchor_y, w=12, h=int(length))
        self.anchor = pygame.Vector2(anchor_x, anchor_y)
        self.length = float(length)
        self.theta = 0.0   # radians from straight down; +ve swings right
        self.omega = 0.0
        self.held = False
        self.hold_radius = self.length
        self.anim_t = 0.0

    def point_at(self, radius: float, theta: float | None = None) -> pygame.Vector2:
        th = self.theta if theta is None else theta
        return self.anchor + pygame.Vector2(math.sin(th), math.cos(th)) * radius

    def tip(self) -> pygame.Vector2:
        return self.point_at(self.length)

    def grab_check(self, grip: pygame.Vector2) -> float | None:
        """Distance along the vine at which *grip* could grab it, or None."""
        tip = self.tip()
        seg = tip - self.anchor
        seg_len_sq = seg.length_squared()
        if seg_len_sq <= 0:
            return None
        t = max(0.0, min(1.0, (grip - self.anchor).dot(seg) / seg_len_sq))
        if t < GRAB_MIN_FRACTION:
            return None
        closest = self.anchor + seg * t
        if (grip - closest).length() > GRAB_RADIUS:
            return None
        return t * self.length

    def update(self, dt: float, world) -> None:
        self.anim_t += dt
        if self.held:
            return
        # Free, lightly damped pendulum back to rest.
        alpha = -(C.GRAVITY / self.length) * math.sin(self.theta)
        self.omega += alpha * dt
        self.omega *= max(0.0, 1.0 - 1.2 * dt)
        self.theta += self.omega * dt
        if abs(self.theta) < 0.002 and abs(self.omega) < 0.01:
            self.theta = self.omega = 0.0

    def draw(self, surf: pygame.Surface, camera) -> None:
        a = camera.world_to_screen(self.anchor)
        end_r = self.hold_radius if self.held else self.length
        # Draw the full rope; the part below the grip hangs on at the same angle.
        segs = max(2, int(self.length // 10))
        prev = a
        for i in range(1, segs + 1):
            r = self.length * i / segs
            wobble = 0.0 if self.held else math.sin(self.anim_t * 2.0 + i * 0.7) * 0.6
            p = camera.world_to_screen(self.point_at(r)) + pygame.Vector2(wobble, 0)
            col = (64, 120, 40) if i % 2 else (48, 98, 32)
            pygame.draw.line(surf, col, prev, p, 3)
            if i % 3 == 0:
                pygame.draw.ellipse(surf, (88, 156, 60), pygame.Rect(int(p.x) + 2, int(p.y) - 3, 8, 5))
            prev = p
        # Knot at the anchor and a leafy grip at the hold point / tip.
        pygame.draw.circle(surf, (96, 56, 30), (int(a.x), int(a.y)), 5)
        grip = camera.world_to_screen(self.point_at(end_r))
        pygame.draw.circle(surf, (110, 170, 70), (int(grip.x), int(grip.y)), 5)
