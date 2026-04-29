"""Level — owns tile grid, entities, parallax background, music key, world bounds."""
from __future__ import annotations

import pygame


class Level:
    def __init__(self, level_id: str) -> None:
        self.level_id = level_id
        self.bounds = pygame.Rect(0, 0, 1, 1)
        self.tile_grid = None  # filled by tilemap loader
        self.entities: list = []
        self.parallax_layers: list = []
        self.music_key: str = ""
        self.spawn_point = pygame.Vector2(0, 0)
