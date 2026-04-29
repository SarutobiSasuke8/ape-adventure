"""World/level metadata. The world map reads this to build its node graph."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LevelEntry:
    id: str
    name: str
    tmx_path: str
    music_key: str
    is_boss: bool = False


@dataclass(frozen=True)
class WorldEntry:
    id: str
    name: str
    palette_key: str
    music_key: str
    levels: tuple[LevelEntry, ...] = field(default_factory=tuple)


WORLD_1 = WorldEntry(
    id="tangle_jungle",
    name="Tangle Jungle",
    palette_key="jungle_warm",
    music_key="tangle_jungle",
    levels=(
        LevelEntry("1-1", "First Steps",       "tangle_jungle/1_1_first_steps.tmx",     "tangle_jungle"),
        LevelEntry("1-2", "Vine Valley",       "tangle_jungle/1_2_vine_valley.tmx",     "tangle_jungle"),
        LevelEntry("1-3", "Hollow Log Run",    "tangle_jungle/1_3_hollow_log_run.tmx",  "tangle_jungle"),
        LevelEntry("1-4", "The Saurian's Arena", "tangle_jungle/1_4_saurian_arena.tmx", "king_saurus", is_boss=True),
    ),
)


ALL_WORLDS: tuple[WorldEntry, ...] = (WORLD_1,)
