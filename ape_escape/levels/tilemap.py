"""pytmx loader. Converts a .tmx file into a Level (tile grid + entity spawns).

Authoring contract (kept in sync with tools/build_levels.py):

  * Tile layer named "collision" (or "solid"/"geometry"): any non-zero tile
    is a SOLID collision block. Tile artwork is irrelevant — the renderer
    draws tiles procedurally from the collision grid, so no tileset image is
    ever loaded.
  * Object group named "entities": every object names an entity via a "kind"
    property (falling back to the object's class/type, then its name). The
    object's (x, y) is the entity's **bottom-centre**, placed on a surface.
    Letters carry a "letter" property; bonus barrels a "sub_level_id".
  * Optional map properties: "level_id", "music_key" (override the defaults).
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytmx

from ape_escape.core.physics import SOLID, TileGrid
from ape_escape.levels.level import Level

_COLLISION_LAYER_NAMES = {"collision", "solid", "geometry"}


def _make_entity(kind: str, props: dict):
    """Construct an entity instance from a tmx object kind + properties.

    Returns the entity placed at (0, 0); the caller seats it on its surface.
    Unknown kinds return None so a bad object can't crash level loading.
    """
    from ape_escape.entities.enemies.snapper import Snapper
    from ape_escape.entities.enemies.hopper import Hopper
    from ape_escape.entities.enemies.slinger import Slinger
    from ape_escape.entities.enemies.king_saurus import KingSaurus
    from ape_escape.entities.collectibles.banana import Banana
    from ape_escape.entities.collectibles.bunch import BananaBunch
    from ape_escape.entities.collectibles.aape_letter import AapeLetter, LETTERS
    from ape_escape.entities.collectibles.bonus_barrel import BonusBarrel
    from ape_escape.entities.collectibles.goal_totem import GoalTotem
    from ape_escape.entities.hazards.spike import Spike

    match kind:
        case "snapper":
            return Snapper(0, 0)
        case "hopper":
            return Hopper(0, 0)
        case "slinger":
            return Slinger(0, 0)
        case "king_saurus":
            return KingSaurus(0, 0)
        case "banana":
            return Banana(0, 0)
        case "bunch":
            return BananaBunch(0, 0)
        case "letter":
            letter = props.get("letter", LETTERS[0])
            if letter not in LETTERS:
                letter = LETTERS[0]
            return AapeLetter(0, 0, letter)
        case "bonus_barrel":
            return BonusBarrel(0, 0, props.get("sub_level_id", ""))
        case "goal_totem":
            return GoalTotem(0, 0)
        case "spike":
            return Spike(0, 0)
        case _:
            return None


def _seat(entity, anchor_x: float, anchor_y: float) -> None:
    """Place *entity* so its bottom-centre sits at (anchor_x, anchor_y)."""
    top_left_x = anchor_x - entity.rect.width / 2.0
    top_left_y = anchor_y - entity.rect.height
    entity.pos = pygame.Vector2(top_left_x, top_left_y)
    entity.rect.topleft = (int(top_left_x), int(top_left_y))


def load_tmx(path: Path | str, *, level_id: str = "", music_key: str = "") -> Level:
    """Load a .tmx tile map and return a populated Level.

    *level_id* / *music_key* supply defaults; map properties of the same name
    override them. Raises FileNotFoundError if the map is missing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"TMX map not found: {path}")

    # pytmx's default image loader is lazy and never opens the tileset image,
    # so a missing/placeholder tileset PNG is fine here.
    tmx = pytmx.TiledMap(str(path))
    map_props = dict(tmx.properties)

    lvl = Level(map_props.get("level_id", level_id) or path.stem)
    lvl.music_key = map_props.get("music_key", music_key) or "tangle_jungle"
    lvl.bounds = pygame.Rect(0, 0, tmx.width * tmx.tilewidth, tmx.height * tmx.tileheight)

    grid = TileGrid(tmx.width, tmx.height, tmx.tilewidth)
    spawn_set = False

    for layer in tmx.layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            if layer.name and layer.name.lower() in _COLLISION_LAYER_NAMES:
                for col, row, gid in layer.iter_data():
                    if gid:
                        grid.set(col, row, SOLID)
        elif isinstance(layer, pytmx.TiledObjectGroup):
            for obj in layer:
                props = dict(obj.properties)
                kind = (props.get("kind") or obj.type or obj.name or "").strip().lower()
                if kind == "spawn":
                    # Spawn point: player top-left, seated above the surface.
                    lvl.spawn_point = pygame.Vector2(obj.x - 14, obj.y - 44)
                    spawn_set = True
                    continue
                entity = _make_entity(kind, props)
                if entity is None:
                    continue
                _seat(entity, obj.x, obj.y)
                lvl.entities.append(entity)

    lvl.tile_grid = grid
    if not spawn_set:
        lvl.spawn_point = pygame.Vector2(2 * tmx.tilewidth, 2 * tmx.tileheight)

    lvl.total_bananas = sum(1 for e in lvl.entities if type(e).__name__ == "Banana")
    lvl.total_letters = sum(1 for e in lvl.entities if type(e).__name__ == "AapeLetter")
    return lvl
