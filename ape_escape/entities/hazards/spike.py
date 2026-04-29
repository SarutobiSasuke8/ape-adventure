"""Spike — instant-death hazard. Most pits/spikes are tile-flagged, but moving spikes are entities."""
from ape_escape.entities.entity import Entity


class Spike(Entity):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=32, h=16)
