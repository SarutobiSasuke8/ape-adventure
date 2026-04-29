"""AudioManager — procedural SFX synth (no external files needed for now)."""
from __future__ import annotations

import math
import struct

import pygame

from ape_adventure.core import constants as C

_SAMPLE_RATE = 44100


def _gen_tone(
    freq: float,
    duration: float,
    wave: str = "sine",
    volume: float = 0.5,
    freq_end: float | None = None,
) -> pygame.mixer.Sound:
    """Generate a mono 16-bit PCM sound buffer."""
    n = int(_SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    attack_n = max(1, int(_SAMPLE_RATE * 0.008))
    release_n = max(1, int(_SAMPLE_RATE * 0.06))

    for i in range(n):
        t = i / _SAMPLE_RATE
        f = freq if freq_end is None else freq + (freq_end - freq) * (i / n)

        if wave == "sine":
            raw = math.sin(2 * math.pi * f * t)
        elif wave == "square":
            raw = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
        elif wave == "saw":
            phase = (f * t) % 1.0
            raw = 2.0 * phase - 1.0
        else:  # noise
            import random
            raw = random.uniform(-1.0, 1.0)

        env = min(1.0, i / attack_n) * min(1.0, (n - i) / release_n)
        val = max(-32768, min(32767, int(raw * env * volume * 32767)))
        struct.pack_into("<h", buf, i * 2, val)

    return pygame.mixer.Sound(buffer=bytes(buf))


def _gen_chord(
    freqs: list[float],
    duration: float,
    volume: float = 0.45,
) -> pygame.mixer.Sound:
    """Mix multiple sine tones into one sound."""
    n = int(_SAMPLE_RATE * duration)
    buf = bytearray(n * 2)
    release_n = max(1, int(_SAMPLE_RATE * 0.12))
    amp = volume / len(freqs)

    for i in range(n):
        t = i / _SAMPLE_RATE
        env = min(1.0, (n - i) / release_n)
        raw = sum(math.sin(2 * math.pi * f * t) for f in freqs)
        val = max(-32768, min(32767, int(raw * env * amp * 32767)))
        struct.pack_into("<h", buf, i * 2, val)

    return pygame.mixer.Sound(buffer=bytes(buf))


class AudioManager:
    def __init__(self) -> None:
        pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._build_sfx()

    def _build_sfx(self) -> None:
        s = self._sfx
        s["jump"]           = _gen_tone(380, 0.12, "sine",   0.40, freq_end=560)
        s["land"]           = _gen_tone(140, 0.08, "sine",   0.35, freq_end=80)
        s["roll"]           = _gen_tone(220, 0.18, "square", 0.25, freq_end=180)
        s["collect_banana"] = _gen_tone(880, 0.13, "sine",   0.40)
        s["collect_letter"] = _gen_chord([660, 880, 1100],   0.30, 0.40)
        s["stomp_enemy"]    = _gen_tone(200, 0.18, "noise",  0.50)
        s["player_hurt"]    = _gen_tone(300, 0.28, "saw",    0.45, freq_end=120)
        s["goal_totem"]     = _gen_chord([523, 659, 784, 1047], 0.60, 0.45)
        s["extra_life"]     = _gen_chord([440, 550, 660, 880], 0.50, 0.50)

    def play(self, key: str) -> None:
        snd = self._sfx.get(key)
        if snd:
            snd.set_volume(C.SFX_VOLUME)
            snd.play()
