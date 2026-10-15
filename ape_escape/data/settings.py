"""Player settings: volume and reduced motion, persisted as JSON.

This is a desktop pygame build, so the browser localStorage pattern maps to a
small JSON file in the per-user data directory (see ``core.paths``):

- Windows: %APPDATA%/ApeAdventure/settings.json
- macOS:   ~/Library/Application Support/ApeAdventure/settings.json
- Linux:   $XDG_DATA_HOME/ApeAdventure/settings.json (default ~/.local/share)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ape_escape.core import constants as C

SETTINGS_FILENAME = "settings.json"
VOLUME_STEP = 0.1


def _clamp_volume(value: object, default: float) -> float:
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return round(min(1.0, max(0.0, v)), 2)


def default_settings_path() -> Path:
    from ape_escape.core.paths import user_data_dir

    return user_data_dir() / SETTINGS_FILENAME


@dataclass
class Settings:
    """User-facing options. ``path=None`` keeps the settings in memory only."""

    music_volume: float = C.MUSIC_VOLUME
    sfx_volume: float = C.SFX_VOLUME
    reduced_motion: bool = False
    path: Path | None = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        """Read settings from *path* (default: user data dir). Missing or
        corrupt files fall back to defaults so the game always starts."""
        if path is None:
            path = default_settings_path()
        settings = cls(path=path)
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return settings
        if not isinstance(data, dict):
            return settings
        settings.music_volume = _clamp_volume(data.get("music_volume"), C.MUSIC_VOLUME)
        settings.sfx_volume = _clamp_volume(data.get("sfx_volume"), C.SFX_VOLUME)
        rm = data.get("reduced_motion", False)
        settings.reduced_motion = rm if isinstance(rm, bool) else False
        return settings

    def to_dict(self) -> dict:
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "reduced_motion": self.reduced_motion,
        }

    def save(self) -> bool:
        """Write to disk. Returns False (and keeps playing) if the write fails."""
        if self.path is None:
            return False
        try:
            target = Path(self.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".tmp")
            tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            tmp.replace(target)
        except OSError:
            return False
        return True

    # ------------------------------------------------------------------
    # Mutators used by the pause menu
    # ------------------------------------------------------------------

    def adjust_music(self, steps: int) -> None:
        self.music_volume = _clamp_volume(self.music_volume + steps * VOLUME_STEP, C.MUSIC_VOLUME)

    def adjust_sfx(self, steps: int) -> None:
        self.sfx_volume = _clamp_volume(self.sfx_volume + steps * VOLUME_STEP, C.SFX_VOLUME)

    def toggle_reduced_motion(self) -> None:
        self.reduced_motion = not self.reduced_motion
