"""Cross-platform user data dir resolution for save files and settings."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "ApeAdventure"


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def package_data_dir() -> Path:
    """In-tree fallback for development."""
    here = Path(__file__).resolve().parent.parent / "data"
    here.mkdir(parents=True, exist_ok=True)
    return here
