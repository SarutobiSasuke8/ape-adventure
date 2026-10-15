"""Settings persistence: round trip, defaults, clamping, corrupt files."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ape_escape.core import constants as C
from ape_escape.data import settings as S
from ape_escape.data.settings import Settings


class SettingsPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "settings.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_file_gives_defaults(self) -> None:
        s = Settings.load(self.path)
        self.assertEqual(s.music_volume, C.MUSIC_VOLUME)
        self.assertEqual(s.sfx_volume, C.SFX_VOLUME)
        self.assertFalse(s.reduced_motion)
        self.assertFalse(self.path.exists())

    def test_round_trip(self) -> None:
        s = Settings.load(self.path)
        s.adjust_music(-3)
        s.adjust_sfx(+1)
        s.toggle_reduced_motion()
        self.assertTrue(s.save())

        again = Settings.load(self.path)
        self.assertAlmostEqual(again.music_volume, 0.3)
        self.assertAlmostEqual(again.sfx_volume, 0.95)
        self.assertTrue(again.reduced_motion)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), again.to_dict())

    def test_volume_is_clamped(self) -> None:
        s = Settings(path=self.path)
        s.adjust_music(-50)
        s.adjust_sfx(+50)
        self.assertEqual(s.music_volume, 0.0)
        self.assertEqual(s.sfx_volume, 1.0)

    def test_out_of_range_and_bad_types_on_disk(self) -> None:
        self.path.write_text(json.dumps({
            "music_volume": 7,
            "sfx_volume": "loud",
            "reduced_motion": "yes",
        }), encoding="utf-8")
        s = Settings.load(self.path)
        self.assertEqual(s.music_volume, 1.0)
        self.assertEqual(s.sfx_volume, C.SFX_VOLUME)
        self.assertFalse(s.reduced_motion)

    def test_corrupt_file_falls_back_to_defaults(self) -> None:
        self.path.write_text("{not json", encoding="utf-8")
        s = Settings.load(self.path)
        self.assertEqual(s.to_dict(), Settings().to_dict())
        # Saving afterwards repairs the file.
        self.assertTrue(s.save())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), s.to_dict())

    def test_non_dict_json_falls_back_to_defaults(self) -> None:
        self.path.write_text("[1, 2, 3]", encoding="utf-8")
        self.assertEqual(Settings.load(self.path).to_dict(), Settings().to_dict())

    def test_in_memory_settings_do_not_write(self) -> None:
        self.assertFalse(Settings().save())

    def test_default_path_is_user_data_dir(self) -> None:
        with mock.patch("ape_escape.core.paths.user_data_dir", return_value=Path(self._tmp.name)):
            self.assertEqual(S.default_settings_path(), self.path)
            s = Settings.load()
            s.toggle_reduced_motion()
            s.save()
        self.assertTrue(self.path.exists())


if __name__ == "__main__":
    unittest.main()
