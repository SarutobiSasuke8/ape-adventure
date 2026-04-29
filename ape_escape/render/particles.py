"""Particle pool — dust, leaf, sparkle, puff.

All particles live in a flat list. No allocation after the pool reaches
capacity (new emits are silently dropped). Each particle is a plain
object with __slots__ so attribute access stays fast.
"""
from __future__ import annotations

import math
import random

import pygame


class _P:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "r", "g", "b", "size", "gravity")

    def __init__(
        self,
        x: float, y: float,
        vx: float, vy: float,
        life: float,
        color: tuple[int, int, int],
        size: float,
        gravity: float,
    ) -> None:
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.life        = life
        self.max_life    = life
        self.r, self.g, self.b = color
        self.size        = size
        self.gravity     = gravity


class ParticleSystem:
    """Emit and update world-space particles, draw them via camera."""

    def __init__(self, capacity: int = 400) -> None:
        self.capacity  = capacity
        self._pool: list[_P] = []

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    def emit(self, kind: str, x: float, y: float, count: int = 1) -> None:
        for _ in range(count):
            if len(self._pool) >= self.capacity:
                return
            if kind == "dust":
                self._dust(x, y)
            elif kind == "leaf":
                self._leaf(x, y)
            elif kind == "sparkle":
                self._sparkle(x, y)
            elif kind == "puff":
                self._puff(x, y)

    def _dust(self, x: float, y: float) -> None:
        angle = random.uniform(math.pi * 0.7, math.pi * 1.3)
        spd   = random.uniform(25, 75)
        self._pool.append(_P(
            x, y,
            math.cos(angle) * spd,
            math.sin(angle) * spd * 0.35,
            random.uniform(0.18, 0.30),
            (random.randint(135, 170), random.randint(105, 135), random.randint(55, 85)),
            random.uniform(2.0, 4.0),
            140,
        ))

    def _leaf(self, x: float, y: float) -> None:
        angle = random.uniform(-math.pi * 0.9, -math.pi * 0.1)
        spd   = random.uniform(45, 105)
        color = random.choice([
            (95,  175, 55),
            (125, 205, 75),
            (75,  155, 45),
            (160, 215, 90),
        ])
        self._pool.append(_P(
            x, y,
            math.cos(angle) * spd,
            math.sin(angle) * spd,
            random.uniform(0.38, 0.55),
            color,
            random.uniform(2.0, 3.5),
            210,
        ))

    def _sparkle(self, x: float, y: float) -> None:
        angle = random.uniform(0, 2 * math.pi)
        spd   = random.uniform(55, 140)
        color = random.choice([
            (255, 240,  80),
            (255, 215,  50),
            (255, 255, 185),
            (250, 180,  40),
        ])
        self._pool.append(_P(
            x, y,
            math.cos(angle) * spd,
            math.sin(angle) * spd,
            random.uniform(0.22, 0.42),
            color,
            random.uniform(2.0, 4.5),
            55,
        ))

    def _puff(self, x: float, y: float) -> None:
        angle = random.uniform(math.pi * 0.6, math.pi * 1.4)
        spd   = random.uniform(35, 105)
        color = random.choice([
            (195, 220, 175),
            (175, 200, 155),
            (210, 230, 190),
        ])
        self._pool.append(_P(
            x, y,
            math.cos(angle) * spd,
            math.sin(angle) * spd,
            random.uniform(0.22, 0.38),
            color,
            random.uniform(3.0, 6.0),
            75,
        ))

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        alive: list[_P] = []
        for p in self._pool:
            p.life -= dt
            if p.life <= 0:
                continue
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            p.vy += p.gravity * dt
            p.vx *= max(0.0, 1.0 - 3.5 * dt)
            alive.append(p)
        self._pool = alive

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface, camera) -> None:
        sw = surf.get_width()
        sh = surf.get_height()
        for p in self._pool:
            frac = p.life / p.max_life
            size = max(1, int(p.size * frac))
            sp   = camera.world_to_screen(pygame.Vector2(p.x, p.y))
            sx, sy = int(sp.x), int(sp.y)
            if sx < -size or sx > sw + size or sy < -size or sy > sh + size:
                continue
            col = (
                min(255, int(p.r * (0.4 + 0.6 * frac))),
                min(255, int(p.g * (0.4 + 0.6 * frac))),
                min(255, int(p.b * (0.4 + 0.6 * frac))),
            )
            pygame.draw.circle(surf, col, (sx, sy), size)
