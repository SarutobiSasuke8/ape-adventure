"""AudioManager — loads music + sfx, handles volume + ducking."""
from __future__ import annotations

from pathlib import Path
import pygame

from ape_adventure.core import constants as C


class AudioManager:
    def __init__(self, asset_root: Path) -> None:
        pygame.mixer.init()
        self.asset_root = asset_root
        self.sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self.current_music_key: str | None = None

    def play_music(self, key: str) -> None:
        # TODO: load assets/music/<key>.ogg, set volume, loop.
        ...

    def play_sfx(self, key: str) -> None:
        # TODO: lazy-load assets/sfx/<key>.wav, play with SFX_VOLUME, duck music briefly for impacts.
        ...
