"""pytmx loader. Converts a .tmx file into a Level (tile grid + entity spawns)."""
from __future__ import annotations

from pathlib import Path

# import pytmx  # noqa  -- enable once dependency is installed


def load_tmx(path: Path):
    """Load a .tmx tile map and return a populated Level. Phase 1.3."""
    raise NotImplementedError("pytmx loader pending — see docs/ROADMAP.md Phase 1.3.")
