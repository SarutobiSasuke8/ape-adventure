"""Music + SFX track metadata. Filenames, base volumes, loop points."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    key: str
    filename: str
    base_volume: float = 1.0
    loop: bool = True


MUSIC_TRACKS: dict[str, Track] = {
    "title":          Track("title",          "title.ogg",          base_volume=0.8),
    "tangle_jungle":  Track("tangle_jungle",  "tangle_jungle.ogg",  base_volume=0.7),
    "king_saurus":    Track("king_saurus",    "king_saurus.ogg",    base_volume=0.85),
}

SFX_TRACKS: dict[str, Track] = {
    "jump":           Track("jump",           "jump.wav",           loop=False),
    "land":           Track("land",           "land.wav",           loop=False),
    "roll":           Track("roll",           "roll.wav",           loop=False),
    "hurt":           Track("hurt",           "hurt.wav",           loop=False),
    "defeat_enemy":   Track("defeat_enemy",   "defeat_enemy.wav",   loop=False),
    "pickup_banana":  Track("pickup_banana",  "pickup_banana.wav",  loop=False),
    "pickup_letter":  Track("pickup_letter",  "pickup_letter.wav",  loop=False),
    "pickup_bunch":   Track("pickup_bunch",   "pickup_bunch.wav",   loop=False),
    "goal_totem":     Track("goal_totem",     "goal_totem.wav",     loop=False),
    "boss_hit":       Track("boss_hit",       "boss_hit.wav",       loop=False),
    "boss_defeated":  Track("boss_defeated",  "boss_defeated.wav",  loop=False),
    "level_clear":    Track("level_clear",    "level_clear.wav",    loop=False),
    "ui_confirm":     Track("ui_confirm",     "ui_confirm.wav",     loop=False),
    "ui_back":        Track("ui_back",        "ui_back.wav",        loop=False),
}
