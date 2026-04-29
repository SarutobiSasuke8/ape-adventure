"""SaveData — persists level clears, best times, and collection records."""
from __future__ import annotations

import json
from pathlib import Path

_SAVE_PATH = Path(__file__).parent / "save.json"


class SaveData:
    """Thin wrapper around a JSON save file.

    Records are written to disk immediately on each clear so a crash
    never loses a completed run.
    """

    def __init__(self) -> None:
        self.cleared:      set[str]         = set()
        self.best_times:   dict[str, float] = {}
        self.best_bananas: dict[str, int]   = {}
        self.best_aape:    dict[str, set[str]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not _SAVE_PATH.exists():
            return
        try:
            data = json.loads(_SAVE_PATH.read_text(encoding="utf-8"))
            self.cleared      = set(data.get("cleared", []))
            self.best_times   = {k: float(v) for k, v in data.get("best_times", {}).items()}
            self.best_bananas = {k: int(v)   for k, v in data.get("best_bananas", {}).items()}
            self.best_aape    = {k: set(v)   for k, v in data.get("best_aape", {}).items()}
        except (json.JSONDecodeError, KeyError, ValueError):
            pass  # corrupt save — silently start fresh

    def _save(self) -> None:
        data = {
            "cleared":      sorted(self.cleared),
            "best_times":   self.best_times,
            "best_bananas": self.best_bananas,
            "best_aape":    {k: sorted(v) for k, v in self.best_aape.items()},
        }
        _SAVE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_clear(
        self,
        level_id: str,
        time: float,
        bananas: int,
        aape: set[str],
    ) -> dict[str, bool]:
        """Update best records for *level_id* and flush to disk.

        Returns a dict of flags so callers can show "new record" feedback:
          ``{"new_time": bool, "new_bananas": bool, "new_aape": bool}``
        """
        flags: dict[str, bool] = {"new_time": False, "new_bananas": False, "new_aape": False}

        self.cleared.add(level_id)

        if level_id not in self.best_times or time < self.best_times[level_id]:
            self.best_times[level_id] = round(time, 2)
            flags["new_time"] = True

        if bananas > self.best_bananas.get(level_id, 0):
            self.best_bananas[level_id] = bananas
            flags["new_bananas"] = True

        prev = self.best_aape.get(level_id, set())
        merged = prev | aape
        if merged != prev:
            self.best_aape[level_id] = merged
            flags["new_aape"] = True

        self._save()
        return flags

    def is_cleared(self, level_id: str) -> bool:
        return level_id in self.cleared

    def best_time(self, level_id: str) -> float | None:
        return self.best_times.get(level_id)

    def best_banana(self, level_id: str) -> int:
        return self.best_bananas.get(level_id, 0)
