"""AudioManager — procedural SFX synth + background music loop."""
from __future__ import annotations

import math
import random
import struct
import threading

import pygame

from ape_escape.core import constants as C

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


def _gen_music_loop() -> pygame.mixer.Sound:
    """Procedural jungle theme — F pentatonic, 110 BPM, 2-bar loop (~4.4s).

    Three voices: bass (square), melody (sine), rhythm (noise bursts).
    Single-pass renderer keeps RAM linear and avoids repeated full-buffer
    passes over the same samples.
    """
    BPM   = 110
    BEAT  = 60.0 / BPM
    LOOP  = BEAT * 8          # 2 bars = 8 beats
    N     = int(_SAMPLE_RATE * LOOP)

    # F pentatonic pitches (Hz)
    F2, A2, C3, D3 = 87.3, 110.0, 130.8, 146.8
    F3, A3, C4, D4, F4 = 174.6, 220.0, 261.6, 293.7, 349.2

    # Build schedule: (start_s, dur_s, freq, wave, vol)
    sched_raw: list[tuple[float, float, float, str, float]] = []

    def add(t_s: float, dur_s: float, freq: float, wave: str = "sine", vol: float = 0.22) -> None:
        sched_raw.append((t_s, dur_s, freq, wave, vol))

    # --- Bass line (square, low volume) ---
    for beat, freq in [
        (0, F2), (1, A2), (2, C3), (3, F2),
        (4, D3), (5, A2), (6, F2), (7, C3),
    ]:
        add(beat * BEAT, BEAT * 0.80, freq, "square", 0.14)

    # --- Melody (sine) ---
    for beat, dur_beats, freq in [
        (0.0, 0.50, F3), (0.5, 0.50, A3), (1.0, 0.75, C4), (1.75, 0.25, A3),
        (2.0, 1.00, F3), (3.0, 1.00, D3),
        (4.0, 0.50, C4), (4.5, 0.50, D4), (5.0, 1.00, F4),
        (6.0, 0.50, D4), (6.5, 0.50, C4), (7.0, 1.00, A3),
    ]:
        add(beat * BEAT, dur_beats * BEAT, freq, "sine", 0.20)

    # --- Rhythm (noise bursts) ---
    for beat in range(8):
        add(beat * BEAT,              0.040, 0.0, "noise", 0.11)   # downbeat
        if beat % 2 == 1:
            add(beat * BEAT + BEAT * 0.5, 0.025, 0.0, "noise", 0.07)  # off-beat

    # Convert to sample-index tuples and sort by start
    sched: list[tuple[int, int, float, str, float]] = sorted(
        [
            (int(s * _SAMPLE_RATE), min(N, int((s + d) * _SAMPLE_RATE)), f, w, v)
            for s, d, f, w, v in sched_raw
        ],
        key=lambda x: x[0],
    )

    # Single-pass render — one loop over N samples
    buf     = bytearray(N * 2)
    active: list[tuple[int, int, float, str, float]] = []
    si      = 0

    for i in range(N):
        # Activate notes whose start sample has arrived
        while si < len(sched) and sched[si][0] <= i:
            active.append(sched[si])
            si += 1

        # Sum contributions from all active notes
        sample      = 0.0
        next_active = []
        for entry in active:
            i0, i1, freq, wave, vol = entry
            if i >= i1:
                continue
            next_active.append(entry)
            li     = i - i0
            n_note = i1 - i0
            lt     = li / _SAMPLE_RATE
            att    = max(1, int(_SAMPLE_RATE * 0.010))
            rel    = max(1, int(_SAMPLE_RATE * 0.060))
            env    = min(1.0, li / att) * min(1.0, (n_note - li) / rel)
            if wave == "sine":
                raw = math.sin(2 * math.pi * freq * lt)
            elif wave == "square":
                raw = 1.0 if math.sin(2 * math.pi * freq * lt) >= 0 else -1.0
            else:   # noise
                raw = random.uniform(-1.0, 1.0)
            sample += raw * env * vol

        active = next_active
        val    = max(-32768, min(32767, int(sample * 32767)))
        struct.pack_into("<h", buf, i * 2, val)

    return pygame.mixer.Sound(buffer=bytes(buf))


class AudioManager:
    def __init__(self) -> None:
        pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
        pygame.mixer.set_num_channels(16)
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._music: pygame.mixer.Sound | None = None
        self._music_channel: pygame.mixer.Channel | None = None
        self._music_ready = threading.Event()
        self._build_sfx()
        # Generate the music loop off-thread so game startup isn't blocked.
        threading.Thread(target=self._build_music, daemon=True).start()

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_music(self) -> None:
        self._music = _gen_music_loop()
        self._music_ready.set()

    def _build_sfx(self) -> None:
        s = self._sfx
        s["jump"]           = _gen_tone(380, 0.12, "sine",   0.40, freq_end=560)
        s["land"]           = _gen_tone(140, 0.08, "sine",   0.35, freq_end=80)
        s["roll"]           = _gen_tone(220, 0.18, "square", 0.25, freq_end=180)
        s["collect_banana"] = _gen_tone(880, 0.13, "sine",   0.40)
        s["collect_letter"] = _gen_chord([660, 880, 1100],        0.30, 0.40)
        s["stomp_enemy"]    = _gen_tone(200, 0.18, "noise",  0.50)
        s["player_hurt"]    = _gen_tone(300, 0.28, "saw",    0.45, freq_end=120)
        s["goal_totem"]     = _gen_chord([523, 659, 784, 1047],   0.60, 0.45)
        s["extra_life"]     = _gen_chord([440, 550, 660, 880],    0.50, 0.50)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, key: str) -> None:
        snd = self._sfx.get(key)
        if snd:
            snd.set_volume(C.SFX_VOLUME)
            snd.play()

    def poll_music(self) -> None:
        """Call once per frame — starts music as soon as the loop is ready.

        No-op if music is already playing or not yet generated.
        """
        if self._music_channel and self._music_channel.get_busy():
            return
        if not self._music_ready.is_set():
            return
        self._music_channel = self._music.play(loops=-1)  # type: ignore[union-attr]
        if self._music_channel:
            self._music_channel.set_volume(C.MUSIC_VOLUME)

    def stop_music(self) -> None:
        if self._music_channel:
            self._music_channel.stop()
            self._music_channel = None
