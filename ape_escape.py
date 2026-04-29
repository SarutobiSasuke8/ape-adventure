"""
╔══════════════════════════════════════════════════════════════════╗
║  LEGACY v0 — APE ESCAPE  (archived, not under active development) ║
║                                                                   ║
║  This is the original single-file arcade prototype. It still      ║
║  runs, but all new work happens in  ape_adventure/               ║
║                                                                   ║
║  To play the real game:   python -m ape_adventure                ║
╚══════════════════════════════════════════════════════════════════╝

APE ESCAPE
A clean, modern 2D arcade platformer — single-file pygame, no external assets.
Run: python ape_escape.py
Controls: Arrow keys / WASD to move, Space to jump, Up/Down on ladders, Esc to quit.
"""

import json
import math
import os
import random
import sys
from enum import Enum

import pygame

# ============================================================
#  CONFIG
# ============================================================
WIDTH, HEIGHT = 960, 720
FPS = 60
TITLE_TEXT = "APE ESCAPE"
HIGHSCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ape_escape_highscore.json"
)

# Palette — saturated, modern, premium
BG_TOP = (10, 14, 32)
BG_MID = (24, 32, 64)
BG_BOTTOM = (44, 56, 100)
BEAM = (236, 86, 78)
BEAM_HI = (255, 142, 130)
BEAM_LO = (158, 46, 40)
BEAM_RIVET = (60, 14, 12)
LADDER = (255, 212, 72)
LADDER_LO = (200, 150, 30)
HERO_BODY = (74, 168, 250)
HERO_BODY_LO = (32, 102, 198)
HERO_HAT = (240, 80, 92)
HERO_HAT_LO = (180, 40, 50)
HERO_SKIN = (255, 222, 184)
APE_BODY = (118, 78, 50)
APE_BODY_LO = (72, 46, 28)
APE_FACE = (220, 200, 168)
APE_EYE = (240, 240, 250)
BARREL = (212, 142, 60)
BARREL_HI = (250, 184, 92)
BARREL_LO = (132, 80, 28)
HAMMER_HEAD = (235, 90, 100)
HAMMER_HANDLE = (180, 130, 80)
HAMMER_GLOW = (255, 240, 150)
DAMSEL_DRESS = (255, 130, 200)
DAMSEL_DRESS_LO = (200, 80, 150)
DAMSEL_SKIN = (255, 222, 200)
DAMSEL_HAIR = (240, 220, 100)
UI_FG = (240, 244, 255)
UI_DIM = (148, 156, 180)
UI_ACCENT = (94, 224, 255)
UI_GOLD = (255, 210, 96)
DANGER = (255, 86, 86)
WHITE = (255, 255, 255)
BLACK = (8, 10, 20)


# ============================================================
#  AUDIO — synthesized tones with a tiny envelope generator
# ============================================================
def synth_sound(freq=440, duration_ms=120, volume=0.35, wave="square", sweep=0.0):
    """Generate a simple sound buffer. sweep adds a frequency glide over the duration."""
    sr = 22050
    n = int(sr * duration_ms / 1000)
    amp = int(32767 * volume)
    buf = bytearray(n * 4)  # 16-bit stereo
    for i in range(n):
        t = i / sr
        f = freq + sweep * (i / n)
        phase = 2 * math.pi * f * t
        if wave == "square":
            v = amp if math.sin(phase) > 0 else -amp
        elif wave == "sine":
            v = int(amp * math.sin(phase))
        elif wave == "saw":
            v = int(amp * (2 * (t * f - math.floor(t * f + 0.5))))
        elif wave == "tri":
            v = int(amp * (2 / math.pi) * math.asin(math.sin(phase)))
        else:  # noise
            v = random.randint(-amp, amp)
        # ADSR-ish envelope
        env = 1.0
        a = n * 0.04
        r = n * 0.35
        if i < a:
            env = i / a
        elif i > n - r:
            env = max(0.0, (n - i) / r)
        v = max(-32767, min(32767, int(v * env)))
        b0 = v & 0xFF
        b1 = (v >> 8) & 0xFF
        idx = i * 4
        buf[idx] = b0
        buf[idx + 1] = b1
        buf[idx + 2] = b0
        buf[idx + 3] = b1
    return pygame.mixer.Sound(buffer=bytes(buf))


class Audio:
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.pre_init(22050, -16, 2, 256)
            pygame.mixer.init()
            self.jump = synth_sound(520, 110, 0.22, "square", sweep=380)
            self.land = synth_sound(180, 60, 0.18, "tri")
            self.smash = synth_sound(120, 220, 0.32, "noise")
            self.pickup = synth_sound(900, 180, 0.30, "sine", sweep=600)
            self.climb = synth_sound(360, 60, 0.10, "tri")
            self.hit = synth_sound(160, 360, 0.40, "saw", sweep=-120)
            self.win_a = synth_sound(660, 140, 0.30, "square")
            self.win_b = synth_sound(880, 140, 0.30, "square")
            self.win_c = synth_sound(1320, 280, 0.30, "square")
            self.barrel_drop = synth_sound(220, 120, 0.20, "tri", sweep=-80)
        except Exception:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        s = getattr(self, name, None)
        if s is not None:
            s.play()


# ============================================================
#  HIGH SCORE PERSISTENCE
# ============================================================
def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("highscore", 0))
    except Exception:
        return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"highscore": int(score)}, f)
    except Exception:
        pass


# ============================================================
#  LEVEL GEOMETRY
# ============================================================
class Platform:
    """A steel beam. tilt is -1 (downhill left), +1 (downhill right) or 0."""

    def __init__(self, x1, x2, y, tilt=0):
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.tilt = tilt
        self.thickness = 14

    def y_at(self, x):
        """Surface y at horizontal position x, accounting for tilt."""
        x = max(self.x1, min(self.x2, x))
        span = self.x2 - self.x1
        if span <= 0:
            return self.y
        t = (x - self.x1) / span  # 0..1
        slope = 18 * self.tilt  # subtle slant
        return self.y - slope / 2 + slope * t

    def covers(self, x):
        return self.x1 - 4 <= x <= self.x2 + 4

    def draw(self, surf):
        # Draw as a thick beam with rivets and shading
        p1 = (self.x1, self.y_at(self.x1))
        p2 = (self.x2, self.y_at(self.x2))
        # Shadow
        pygame.draw.line(
            surf,
            BEAM_LO,
            (p1[0], p1[1] + self.thickness // 2 + 2),
            (p2[0], p2[1] + self.thickness // 2 + 2),
            self.thickness,
        )
        # Main beam
        pygame.draw.line(surf, BEAM, p1, p2, self.thickness)
        # Highlight stripe
        pygame.draw.line(
            surf,
            BEAM_HI,
            (p1[0], p1[1] - self.thickness // 4),
            (p2[0], p2[1] - self.thickness // 4),
            2,
        )
        # Rivets
        span = self.x2 - self.x1
        steps = max(2, int(span // 60))
        for i in range(steps + 1):
            rx = self.x1 + (span * i / steps)
            ry = self.y_at(rx)
            pygame.draw.circle(surf, BEAM_RIVET, (int(rx), int(ry + 2)), 2)
            pygame.draw.circle(surf, BEAM_HI, (int(rx) - 1, int(ry + 1)), 1)


class Ladder:
    """Vertical climbable connector between two platforms."""

    def __init__(self, x, top_plat, bottom_plat, width=28):
        self.x = x
        self.top = top_plat
        self.bottom = bottom_plat
        self.width = width
        self.y_top = top_plat.y_at(x)
        self.y_bottom = bottom_plat.y_at(x)

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.width // 2,
            self.y_top,
            self.width,
            self.y_bottom - self.y_top,
        )

    def draw(self, surf):
        x = self.x
        # Side rails
        pygame.draw.line(
            surf, LADDER_LO, (x - self.width / 2, self.y_top), (x - self.width / 2, self.y_bottom), 5
        )
        pygame.draw.line(
            surf, LADDER, (x - self.width / 2 + 1, self.y_top), (x - self.width / 2 + 1, self.y_bottom), 3
        )
        pygame.draw.line(
            surf, LADDER_LO, (x + self.width / 2, self.y_top), (x + self.width / 2, self.y_bottom), 5
        )
        pygame.draw.line(
            surf, LADDER, (x + self.width / 2 - 1, self.y_top), (x + self.width / 2 - 1, self.y_bottom), 3
        )
        # Rungs
        rungs = max(3, int((self.y_bottom - self.y_top) / 22))
        for i in range(1, rungs):
            ry = self.y_top + (self.y_bottom - self.y_top) * (i / rungs)
            pygame.draw.line(
                surf, LADDER_LO, (x - self.width / 2, ry + 1), (x + self.width / 2, ry + 1), 4
            )
            pygame.draw.line(
                surf, LADDER, (x - self.width / 2, ry), (x + self.width / 2, ry), 3
            )


def build_level():
    """Create platforms and ladders. Returns (platforms, ladders, hammer_spot, ape_spot, damsel_spot)."""
    plats = []
    floor_ys = [660, 560, 460, 360, 260, 160]
    tilts = [+1, -1, +1, -1, +1, 0]
    for i, (y, tilt) in enumerate(zip(floor_ys, tilts)):
        margin = 60
        if i == len(floor_ys) - 1:
            # Top platform — narrower stage for ape & damsel
            plats.append(Platform(220, 740, y, 0))
        else:
            plats.append(Platform(margin, WIDTH - margin, y, tilt))

    ladders = []
    # Alternate ladder positions, leaving the platform gaps interesting
    ladder_xs = [WIDTH - 130, 150, WIDTH - 180, 180, WIDTH - 220]
    for i, lx in enumerate(ladder_xs):
        ladders.append(Ladder(lx, plats[i + 1], plats[i]))

    # Optional second ladder on lowest tier for variety
    ladders.append(Ladder(220, plats[1], plats[0]))

    hammer_spot = (WIDTH // 2 - 60, plats[2].y_at(WIDTH // 2 - 60) - 26)
    ape_spot = (300, plats[5].y_at(300))
    damsel_spot = (640, plats[5].y_at(640))
    return plats, ladders, hammer_spot, ape_spot, damsel_spot


# ============================================================
#  ENTITIES
# ============================================================
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")

    def __init__(self, x, y, vx, vy, life, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 280 * dt
        self.vx *= 0.96
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        a = max(0.0, min(1.0, self.life / self.max_life))
        s = max(1, int(self.size * a))
        col = (
            int(self.color[0]),
            int(self.color[1]),
            int(self.color[2]),
        )
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), s)


class Hero:
    WIDTH = 26
    HEIGHT = 38

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.on_ladder = False
        self.facing = 1
        self.platform = None
        self.has_hammer = False
        self.hammer_time = 0.0
        self.hammer_swing = 0.0
        self.alive = True
        self.win = False
        self.anim = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.WIDTH / 2), int(self.y - self.HEIGHT), self.WIDTH, self.HEIGHT)

    @property
    def hammer_rect(self):
        if not self.has_hammer:
            return None
        # Hammer extends from hero's hands; alternates up/down via hammer_swing
        swing = math.sin(self.hammer_swing * math.pi * 2)
        offset_y = -10 + swing * 20  # swings -30..+10
        ox = self.facing * 22
        return pygame.Rect(
            int(self.x + ox - 14),
            int(self.y - self.HEIGHT / 2 + offset_y),
            28,
            28,
        )

    def grab_hammer(self):
        self.has_hammer = True
        self.hammer_time = 7.5
        self.hammer_swing = 0.0

    def update(self, dt, keys, platforms, ladders, audio):
        if not self.alive or self.win:
            return

        # --- Horizontal input ---
        moving = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            moving = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            moving = 1

        # --- Ladder logic ---
        ladder_at = self._ladder_at(ladders)
        wants_climb = (keys[pygame.K_UP] or keys[pygame.K_w]) and not self.has_hammer
        wants_descend = (keys[pygame.K_DOWN] or keys[pygame.K_s]) and not self.has_hammer

        if self.on_ladder:
            self.vx = 0
            self.vy = 0
            if wants_climb:
                self.vy = -110
                self.anim += dt * 6
            elif wants_descend:
                self.vy = 110
                self.anim += dt * 6
            # allow stepping off horizontally only when aligned with platform
            if moving != 0 and ladder_at is None:
                self.on_ladder = False
            self.x += self.vx * dt
            self.y += self.vy * dt
            # Snap off ladder when reaching top/bottom platform surface
            if ladder_at is None:
                self.on_ladder = False
            else:
                if self.y <= ladder_at.y_top:
                    self.y = ladder_at.y_top
                    self.on_ladder = False
                    self.platform = ladder_at.top
                    self.on_ground = True
                if self.y >= ladder_at.y_bottom:
                    self.y = ladder_at.y_bottom
                    self.on_ladder = False
                    self.platform = ladder_at.bottom
                    self.on_ground = True
            return

        # --- Try to mount a ladder ---
        if ladder_at is not None:
            if wants_climb and self.y > ladder_at.y_top + 4:
                self.on_ladder = True
                self.x = ladder_at.x
                self.vy = 0
                audio.play("climb")
                return
            if wants_descend and self.on_ground and self.y < ladder_at.y_bottom - 4:
                self.on_ladder = True
                self.x = ladder_at.x
                self.y += 4
                self.vy = 0
                audio.play("climb")
                return

        # --- Standard platforming ---
        target_vx = moving * 220
        # Hammer mode: slower
        if self.has_hammer:
            target_vx *= 0.78
        self.vx += (target_vx - self.vx) * min(1.0, dt * 18)
        if moving != 0:
            self.facing = moving
            self.anim += dt * 10

        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.on_ground and not self.has_hammer:
            self.vy = -430
            self.on_ground = False
            self.platform = None
            audio.play("jump")

        # Gravity
        self.vy += 1400 * dt
        if self.vy > 900:
            self.vy = 900

        prev_y = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Clamp horizontally to screen
        self.x = max(20, min(WIDTH - 20, self.x))

        # Land on platforms (only when falling)
        landed_now = False
        self.on_ground = False
        if self.vy >= 0:
            for p in platforms:
                if not p.covers(self.x):
                    continue
                surface_y = p.y_at(self.x)
                if prev_y - 2 <= surface_y <= self.y + 1:
                    self.y = surface_y
                    self.vy = 0
                    self.on_ground = True
                    self.platform = p
                    landed_now = True
                    break
        if landed_now and abs(prev_y - self.y) > 6:
            audio.play("land")

        # Hammer countdown
        if self.has_hammer:
            self.hammer_time -= dt
            self.hammer_swing += dt * 2.5
            if self.hammer_time <= 0:
                self.has_hammer = False

    def _ladder_at(self, ladders):
        for l in ladders:
            if abs(self.x - l.x) < l.width / 2 + 4 and l.y_top - 6 <= self.y <= l.y_bottom + 6:
                return l
        return None

    def draw(self, surf):
        if not self.alive and not self.win:
            return
        cx, cy = self.x, self.y
        bob = math.sin(self.anim) * 1.5 if self.on_ground else 0
        # Legs
        leg_split = math.sin(self.anim) * 4 if self.on_ground and abs(self.vx) > 4 else 0
        pygame.draw.line(
            surf, HERO_BODY_LO, (cx - 5 + leg_split, cy - 8), (cx - 5 + leg_split, cy - 1), 5
        )
        pygame.draw.line(
            surf, HERO_BODY_LO, (cx + 5 - leg_split, cy - 8), (cx + 5 - leg_split, cy - 1), 5
        )
        # Body (overalls)
        body_rect = pygame.Rect(int(cx - 11), int(cy - 24 + bob), 22, 18)
        pygame.draw.rect(surf, HERO_BODY, body_rect, border_radius=5)
        pygame.draw.rect(surf, HERO_BODY_LO, body_rect, width=2, border_radius=5)
        # Buttons
        pygame.draw.circle(surf, UI_GOLD, (int(cx - 4), int(cy - 14 + bob)), 2)
        pygame.draw.circle(surf, UI_GOLD, (int(cx + 4), int(cy - 14 + bob)), 2)
        # Head
        head_y = int(cy - 30 + bob)
        pygame.draw.circle(surf, HERO_SKIN, (int(cx), head_y), 8)
        pygame.draw.circle(surf, HERO_BODY_LO, (int(cx), head_y), 8, 1)
        # Hat
        hat_rect = pygame.Rect(int(cx - 10), int(head_y - 10), 20, 7)
        pygame.draw.rect(surf, HERO_HAT, hat_rect, border_radius=3)
        pygame.draw.rect(surf, HERO_HAT_LO, hat_rect, width=1, border_radius=3)
        brim = pygame.Rect(int(cx - 12 + self.facing * 2), int(head_y - 4), 14, 3)
        pygame.draw.rect(surf, HERO_HAT, brim, border_radius=2)
        # Eye
        eye_x = int(cx + self.facing * 3)
        pygame.draw.circle(surf, BLACK, (eye_x, head_y), 1)
        # Mustache
        pygame.draw.line(surf, BLACK, (cx - 3, head_y + 3), (cx + 3, head_y + 3), 2)
        # Arms
        arm_swing = math.sin(self.anim) * 4 if self.on_ground and abs(self.vx) > 4 else 0
        pygame.draw.line(
            surf, HERO_BODY, (cx - 11, cy - 18 + bob), (cx - 13, cy - 12 + bob + arm_swing), 4
        )
        pygame.draw.line(
            surf, HERO_BODY, (cx + 11, cy - 18 + bob), (cx + 13, cy - 12 + bob - arm_swing), 4
        )
        # Hammer
        if self.has_hammer:
            self._draw_hammer(surf, cx, cy)

    def _draw_hammer(self, surf, cx, cy):
        swing = math.sin(self.hammer_swing * math.pi * 2)
        ox = self.facing * 18
        head_y = cy - 22 + swing * 18
        # Glow
        for r, a in [(22, 40), (16, 70)]:
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*HAMMER_GLOW, a), (r, r), r)
            surf.blit(glow, (cx + ox - r, head_y - r))
        # Handle
        pygame.draw.line(
            surf, HAMMER_HANDLE, (cx, cy - 20), (cx + ox, head_y), 4
        )
        # Head
        head_rect = pygame.Rect(int(cx + ox - 12), int(head_y - 8), 24, 16)
        pygame.draw.rect(surf, HAMMER_HEAD, head_rect, border_radius=3)
        pygame.draw.rect(surf, HERO_HAT_LO, head_rect, width=2, border_radius=3)


class Barrel:
    RADIUS = 14

    def __init__(self, x, y, platform, direction):
        self.x = x
        self.y = y
        self.vx = 70 * direction
        self.vy = 0
        self.platform = platform
        self.direction = direction
        self.on_ground = True
        self.alive = True
        self.rotation = 0.0
        self.smashed = False
        self.smash_timer = 0.0
        self.scored_floors = set()
        if platform is not None:
            self.scored_floors.add(id(platform))

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.RADIUS), int(self.y - self.RADIUS * 2), self.RADIUS * 2, self.RADIUS * 2)

    def update(self, dt, platforms, ladders, speed_mul):
        if self.smashed:
            self.smash_timer -= dt
            if self.smash_timer <= 0:
                self.alive = False
            return

        # Roll
        if self.on_ground and self.platform is not None:
            roll_speed = (90 + 35 * abs(self.platform.tilt)) * speed_mul
            self.vx = self.direction * roll_speed
            # If platform is tilted, accelerate down the slope
            if self.platform.tilt != 0:
                self.direction = self.platform.tilt
            self.x += self.vx * dt
            self.rotation += (self.vx / self.RADIUS) * dt * 0.4
            self.y = self.platform.y_at(self.x)

            # Random chance to drop down a ladder if aligned
            for l in ladders:
                if (
                    l.top is self.platform
                    and abs(self.x - l.x) < 8
                    and random.random() < 0.012
                ):
                    self.platform = None
                    self.on_ground = False
                    self.vx = 0
                    self.vy = 60
                    return

            # Fall off edge
            if self.x < self.platform.x1 or self.x > self.platform.x2:
                self.platform = None
                self.on_ground = False
                self.vy = 30
        else:
            # Falling
            self.vy += 1300 * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.rotation += dt * 4
            # Land on a platform
            for p in platforms:
                if not p.covers(self.x):
                    continue
                surf_y = p.y_at(self.x)
                if (self.y - self.vy * dt) <= surf_y <= self.y + 4 and self.vy > 0:
                    self.y = surf_y
                    self.vy = 0
                    self.on_ground = True
                    self.platform = p
                    if p.tilt != 0:
                        self.direction = p.tilt
                    else:
                        self.direction = 1 if self.direction >= 0 else -1
                    break

        # Off-screen cleanup
        if self.y > HEIGHT + 60 or self.x < -60 or self.x > WIDTH + 60:
            self.alive = False

    def smash(self):
        self.smashed = True
        self.smash_timer = 0.35

    def draw(self, surf):
        if self.smashed:
            # Draw expanding ring
            r = int(8 + (0.35 - self.smash_timer) * 60)
            a = max(0, int(255 * (self.smash_timer / 0.35)))
            ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*BARREL_HI, a), (r + 2, r + 2), r, 3)
            surf.blit(ring, (self.x - r - 2, self.y - r - 2))
            return

        cx, cy = int(self.x), int(self.y - self.RADIUS)
        # Shadow
        shadow = pygame.Surface((self.RADIUS * 3, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surf.blit(shadow, (cx - self.RADIUS * 1.5, self.y - 2))

        # Body
        body_rect = pygame.Rect(cx - self.RADIUS, cy - self.RADIUS + 2, self.RADIUS * 2, self.RADIUS * 2 - 4)
        pygame.draw.ellipse(surf, BARREL, body_rect)
        pygame.draw.ellipse(surf, BARREL_LO, body_rect, 2)
        # Stripes that rotate
        for i in range(-1, 2):
            ang = self.rotation + i * 1.0
            ox = math.cos(ang) * self.RADIUS * 0.7
            stripe_rect = pygame.Rect(int(cx + ox - 2), cy - self.RADIUS + 4, 4, self.RADIUS * 2 - 8)
            color = BARREL_HI if i == 0 else BARREL_LO
            pygame.draw.rect(surf, color, stripe_rect, border_radius=2)
        # Top/bottom rim highlight
        pygame.draw.line(
            surf, BARREL_HI, (cx - self.RADIUS + 2, cy - self.RADIUS + 3), (cx + self.RADIUS - 2, cy - self.RADIUS + 3), 1
        )


class Ape:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.anim = 0.0
        self.throw_anim = 0.0
        self.facing = 1

    def trigger_throw(self):
        self.throw_anim = 0.8

    def update(self, dt):
        self.anim += dt
        if self.throw_anim > 0:
            self.throw_anim = max(0.0, self.throw_anim - dt)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        bob = math.sin(self.anim * 2) * 2
        throw_lift = math.sin(min(1.0, (0.8 - self.throw_anim) / 0.8) * math.pi) * 14 if self.throw_anim > 0 else 0
        # Body
        body_rect = pygame.Rect(cx - 36, cy - 70 + bob, 72, 56)
        pygame.draw.rect(surf, APE_BODY_LO, body_rect.inflate(4, 4), border_radius=12)
        pygame.draw.rect(surf, APE_BODY, body_rect, border_radius=12)
        # Belly
        belly = pygame.Rect(cx - 18, cy - 52 + bob, 36, 30)
        pygame.draw.ellipse(surf, APE_FACE, belly)
        # Head
        head = pygame.Rect(cx - 24, cy - 100 + bob, 48, 40)
        pygame.draw.ellipse(surf, APE_BODY_LO, head.inflate(4, 4))
        pygame.draw.ellipse(surf, APE_BODY, head)
        # Face
        face = pygame.Rect(cx - 14, cy - 86 + bob, 28, 22)
        pygame.draw.ellipse(surf, APE_FACE, face)
        # Eyes (angry)
        eye_y = cy - 84 + bob
        pygame.draw.circle(surf, APE_EYE, (cx - 8, eye_y), 4)
        pygame.draw.circle(surf, APE_EYE, (cx + 8, eye_y), 4)
        pygame.draw.circle(surf, BLACK, (cx - 7, eye_y), 2)
        pygame.draw.circle(surf, BLACK, (cx + 7, eye_y), 2)
        # Brows
        pygame.draw.line(surf, BLACK, (cx - 12, eye_y - 5), (cx - 4, eye_y - 2), 3)
        pygame.draw.line(surf, BLACK, (cx + 4, eye_y - 2), (cx + 12, eye_y - 5), 3)
        # Mouth
        pygame.draw.arc(surf, BLACK, (cx - 9, cy - 78 + bob, 18, 12), math.pi, 2 * math.pi, 2)
        pygame.draw.line(surf, BLACK, (cx - 6, cy - 70 + bob), (cx + 6, cy - 70 + bob), 2)
        # Arms
        arm_y = cy - 50 + bob
        # Left arm
        pygame.draw.line(surf, APE_BODY, (cx - 30, arm_y), (cx - 44, cy - 30 + bob), 10)
        # Right arm — lifts barrel when throwing
        if self.throw_anim > 0:
            pygame.draw.line(
                surf,
                APE_BODY,
                (cx + 30, arm_y),
                (cx + 46, cy - 86 + bob - throw_lift),
                10,
            )
            pygame.draw.circle(surf, BARREL, (cx + 50, cy - 92 + bob - throw_lift), 12)
            pygame.draw.circle(surf, BARREL_LO, (cx + 50, cy - 92 + bob - throw_lift), 12, 2)
        else:
            pygame.draw.line(surf, APE_BODY, (cx + 30, arm_y), (cx + 44, cy - 30 + bob), 10)
        # Feet
        pygame.draw.ellipse(surf, APE_BODY_LO, (cx - 30, cy - 18, 22, 12))
        pygame.draw.ellipse(surf, APE_BODY_LO, (cx + 8, cy - 18, 22, 12))


class Damsel:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.anim = 0.0
        self.help_visible = True
        self.help_timer = 0.0

    def update(self, dt):
        self.anim += dt
        self.help_timer += dt
        if self.help_timer > 1.6:
            self.help_visible = not self.help_visible
            self.help_timer = 0.0

    def draw(self, surf, fonts):
        cx, cy = int(self.x), int(self.y)
        bob = math.sin(self.anim * 1.6) * 2
        # Dress
        dress = [
            (cx - 14, cy - 8 + bob),
            (cx + 14, cy - 8 + bob),
            (cx + 18, cy),
            (cx - 18, cy),
        ]
        pygame.draw.polygon(surf, DAMSEL_DRESS_LO, [(p[0], p[1] + 2) for p in dress])
        pygame.draw.polygon(surf, DAMSEL_DRESS, dress)
        # Torso
        torso = pygame.Rect(cx - 8, cy - 22 + bob, 16, 16)
        pygame.draw.rect(surf, DAMSEL_DRESS, torso, border_radius=4)
        # Head
        pygame.draw.circle(surf, DAMSEL_SKIN, (cx, cy - 28 + bob), 8)
        # Hair
        pygame.draw.arc(surf, DAMSEL_HAIR, (cx - 9, cy - 38 + bob, 18, 18), 0, math.pi, 5)
        pygame.draw.circle(surf, DAMSEL_HAIR, (cx - 8, cy - 26 + bob), 4)
        pygame.draw.circle(surf, DAMSEL_HAIR, (cx + 8, cy - 26 + bob), 4)
        # Eyes
        pygame.draw.circle(surf, BLACK, (cx - 3, cy - 28 + bob), 1)
        pygame.draw.circle(surf, BLACK, (cx + 3, cy - 28 + bob), 1)
        # Arms up (calling for help)
        pygame.draw.line(surf, DAMSEL_SKIN, (cx - 8, cy - 16 + bob), (cx - 14, cy - 30 + bob), 4)
        pygame.draw.line(surf, DAMSEL_SKIN, (cx + 8, cy - 16 + bob), (cx + 14, cy - 30 + bob), 4)
        # HELP! bubble
        if self.help_visible:
            txt = fonts["small"].render("HELP!", True, DANGER)
            bubble_rect = txt.get_rect(center=(cx, cy - 56 + int(bob)))
            pad = pygame.Rect(bubble_rect.left - 8, bubble_rect.top - 4, bubble_rect.width + 16, bubble_rect.height + 8)
            pygame.draw.rect(surf, WHITE, pad, border_radius=8)
            pygame.draw.rect(surf, DANGER, pad, width=2, border_radius=8)
            surf.blit(txt, bubble_rect)


class Hammer:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.bob = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 22), 32, 32)

    def update(self, dt):
        self.bob += dt

    def draw(self, surf):
        if not self.alive:
            return
        bob = math.sin(self.bob * 2.5) * 4
        cx, cy = int(self.x), int(self.y + bob)
        # Glow halo
        for r, a in [(28, 40), (20, 80), (14, 130)]:
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*HAMMER_GLOW, a), (r, r), r)
            surf.blit(glow, (cx - r, cy - r))
        # Handle
        pygame.draw.line(surf, HAMMER_HANDLE, (cx, cy + 12), (cx, cy - 6), 5)
        pygame.draw.line(surf, BLACK, (cx, cy + 12), (cx, cy - 6), 1)
        # Head
        head = pygame.Rect(cx - 14, cy - 16, 28, 14)
        pygame.draw.rect(surf, HAMMER_HEAD, head, border_radius=3)
        pygame.draw.rect(surf, BLACK, head, width=2, border_radius=3)
        pygame.draw.line(surf, HAMMER_GLOW, (cx - 10, cy - 14), (cx + 8, cy - 14), 2)


# ============================================================
#  GAME STATES
# ============================================================
class State(Enum):
    TITLE = 1
    PLAYING = 2
    DYING = 3
    LEVEL_COMPLETE = 4
    GAME_OVER = 5


# ============================================================
#  MAIN GAME
# ============================================================
class ApeEscape:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE_TEXT)
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.fonts = {
            "huge": pygame.font.SysFont("arialblack,arial", 96, bold=True),
            "big": pygame.font.SysFont("arialblack,arial", 56, bold=True),
            "med": pygame.font.SysFont("arial", 32, bold=True),
            "small": pygame.font.SysFont("arial", 20, bold=True),
            "tiny": pygame.font.SysFont("arial", 14, bold=True),
        }
        self.bg = self._build_background()
        self.shake = 0.0
        self.particles = []
        self.floating_texts = []
        self.highscore = load_highscore()
        self.state = State.TITLE
        self.title_blink = 0.0
        self.start_button = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 230, 260, 64)
        self.reset_run()

    def reset_run(self):
        self.score = 0
        self.lives = 3
        self.level_num = 1
        self._setup_level()

    def _setup_level(self):
        self.platforms, self.ladders, hammer_spot, ape_spot, damsel_spot = build_level()
        bottom = self.platforms[0]
        self.hero = Hero(120, bottom.y_at(120))
        self.barrels = []
        self.hammer = Hammer(*hammer_spot)
        self.ape = Ape(*ape_spot)
        self.damsel = Damsel(*damsel_spot)
        self.barrel_timer = 1.4
        self.level_timer = 0.0
        self.height_award = set()
        self.particles.clear()
        self.shake = 0.0
        self.death_timer = 0.0
        self.win_timer = 0.0
        self.speed_mul = 1.0 + (self.level_num - 1) * 0.18

    def _build_background(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        # Vertical gradient
        for y in range(HEIGHT):
            t = y / HEIGHT
            if t < 0.5:
                k = t / 0.5
                r = int(BG_TOP[0] + (BG_MID[0] - BG_TOP[0]) * k)
                g = int(BG_TOP[1] + (BG_MID[1] - BG_TOP[1]) * k)
                b = int(BG_TOP[2] + (BG_MID[2] - BG_TOP[2]) * k)
            else:
                k = (t - 0.5) / 0.5
                r = int(BG_MID[0] + (BG_BOTTOM[0] - BG_MID[0]) * k)
                g = int(BG_MID[1] + (BG_BOTTOM[1] - BG_MID[1]) * k)
                b = int(BG_MID[2] + (BG_BOTTOM[2] - BG_MID[2]) * k)
            pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
        # Subtle stars
        random.seed(7)
        for _ in range(60):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT // 2)
            br = random.randint(80, 200)
            pygame.draw.circle(bg, (br, br, br + 20), (sx, sy), 1)
        random.seed()
        # Subtle grid (blueprint style)
        grid = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in range(0, WIDTH, 40):
            pygame.draw.line(grid, (255, 255, 255, 8), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(grid, (255, 255, 255, 8), (0, y), (WIDTH, y), 1)
        bg.blit(grid, (0, 0))
        return bg

    # ------- main loop -------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 30.0)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.state == State.PLAYING:
                        self.state = State.TITLE
                    else:
                        pygame.quit()
                        sys.exit()
                if self.state == State.TITLE and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._start_game()
                if self.state == State.GAME_OVER and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = State.TITLE
                if self.state == State.LEVEL_COMPLETE and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.level_num += 1
                    self._setup_level()
                    self.state = State.PLAYING
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.state == State.TITLE and self.start_button.collidepoint(e.pos):
                    self._start_game()

    def _start_game(self):
        self.reset_run()
        self.state = State.PLAYING
        self.audio.play("pickup")

    # ------- update -------
    def _update(self, dt):
        self.title_blink += dt
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 8)
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        if self.state == State.PLAYING:
            self._update_play(dt)
        elif self.state == State.DYING:
            self.death_timer -= dt
            self.hero.y -= 50 * dt
            if self.death_timer <= 0:
                if self.lives <= 0:
                    if self.score > self.highscore:
                        self.highscore = self.score
                        save_highscore(self.highscore)
                    self.state = State.GAME_OVER
                else:
                    self._respawn()
        elif self.state == State.LEVEL_COMPLETE:
            self.win_timer -= dt
            self.damsel.update(dt)
        elif self.state == State.TITLE:
            # Animate ape on title
            self.ape.update(dt)

    def _update_play(self, dt):
        keys = pygame.key.get_pressed()
        self.hero.update(dt, keys, self.platforms, self.ladders, self.audio)
        self.ape.update(dt)
        self.damsel.update(dt)
        self.hammer.update(dt)
        self.level_timer += dt

        # Award score when hero reaches a new floor
        if self.hero.platform is not None:
            idx = self.platforms.index(self.hero.platform) if self.hero.platform in self.platforms else -1
            if idx > 0 and idx not in self.height_award:
                self.height_award.add(idx)
                self._add_score(100, self.hero.x, self.hero.y - 30)

        # Spawn barrels
        self.barrel_timer -= dt
        if self.barrel_timer <= 0:
            self._spawn_barrel()
            self.barrel_timer = max(0.7, 2.4 - 0.18 * self.level_num) + random.uniform(-0.3, 0.4)

        # Update barrels
        for b in self.barrels:
            b.update(dt, self.platforms, self.ladders, self.speed_mul)
        # Score floor crossings of barrels (not used for player score, just visuals)

        # Hammer collision
        if self.hammer.alive and self.hero.rect.colliderect(self.hammer.rect):
            self.hammer.alive = False
            self.hero.grab_hammer()
            self.audio.play("pickup")
            self._add_score(300, self.hammer.x, self.hammer.y)
            self._burst(self.hammer.x, self.hammer.y, HAMMER_GLOW, count=18)
            self.shake = 0.6

        # Barrel-hero / barrel-hammer collisions
        hero_rect = self.hero.rect
        hammer_rect = self.hero.hammer_rect if self.hero.has_hammer else None
        for b in self.barrels:
            if b.smashed:
                continue
            br = b.rect
            if hammer_rect is not None and hammer_rect.colliderect(br):
                b.smash()
                self.audio.play("smash")
                self._add_score(500, b.x, b.y - 12)
                self._burst(b.x, b.y - 10, BARREL_HI, count=14)
                self.shake = 0.5
                continue
            if hero_rect.colliderect(br) and self.hero.alive:
                self._kill_hero()
                break

        # Win condition
        if hero_rect.colliderect(pygame.Rect(self.damsel.x - 22, self.damsel.y - 40, 44, 50)):
            self._win_level()

        # Cull dead barrels
        self.barrels = [b for b in self.barrels if b.alive]

    def _spawn_barrel(self):
        top = self.platforms[-1]
        sx = self.ape.x + 40
        sy = top.y_at(sx) - 4
        direction = 1 if top.tilt >= 0 else -1
        # randomize direction sometimes
        if random.random() < 0.18:
            direction = -direction
        b = Barrel(sx, sy, top, direction)
        self.barrels.append(b)
        self.ape.trigger_throw()
        self.audio.play("barrel_drop")

    def _kill_hero(self):
        self.hero.alive = False
        self.lives -= 1
        self.state = State.DYING
        self.death_timer = 1.4
        self.audio.play("hit")
        self.shake = 1.2
        for _ in range(28):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(80, 240)
            self.particles.append(
                Particle(
                    self.hero.x,
                    self.hero.y - 18,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 60,
                    random.uniform(0.5, 1.0),
                    random.randint(2, 4),
                    random.choice([HERO_BODY, HERO_HAT, HERO_SKIN, UI_GOLD]),
                )
            )

    def _respawn(self):
        bottom = self.platforms[0]
        self.hero = Hero(120, bottom.y_at(120))
        self.barrels.clear()
        self.barrel_timer = 1.6
        self.height_award.clear()
        self.state = State.PLAYING

    def _win_level(self):
        if self.state == State.LEVEL_COMPLETE:
            return
        self.state = State.LEVEL_COMPLETE
        self.win_timer = 4.0
        bonus = max(500, int(5000 - self.level_timer * 50))
        self._add_score(bonus, self.damsel.x, self.damsel.y - 50)
        self.audio.play("win_a")
        pygame.time.set_timer(pygame.USEREVENT + 1, 200, loops=1)
        # play short fanfare via chained sounds (simple)
        pygame.time.set_timer(pygame.USEREVENT + 2, 220, loops=1)
        self.audio.play("win_b")
        self.audio.play("win_c")
        self.shake = 1.0
        self._burst(self.damsel.x, self.damsel.y - 20, DAMSEL_DRESS, count=40)
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)

    def _add_score(self, amount, x=None, y=None):
        self.score += amount
        if x is not None:
            self.floating_texts.append((amount, x, y, 1.0))

    def _burst(self, x, y, color, count=12):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(60, 220)
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 40,
                    random.uniform(0.4, 0.9),
                    random.randint(2, 5),
                    color,
                )
            )

    # ------- draw -------
    def _draw(self):
        ox = oy = 0
        if self.shake > 0:
            ox = int((random.random() - 0.5) * self.shake * 16)
            oy = int((random.random() - 0.5) * self.shake * 16)

        self.screen.blit(self.bg, (0, 0))

        # Steel construction-girder backdrop
        self._draw_backdrop_supports()

        for l in self.ladders:
            l.draw(self.screen)
        for p in self.platforms:
            p.draw(self.screen)

        if self.state in (State.PLAYING, State.DYING, State.LEVEL_COMPLETE):
            self.hammer.draw(self.screen)
            self.ape.draw(self.screen)
            self.damsel.draw(self.screen, self.fonts)
            for b in self.barrels:
                b.draw(self.screen)
            self.hero.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)
        # Floating score texts
        new_floats = []
        for (amt, fx, fy, life) in self.floating_texts:
            life -= 1 / FPS
            if life <= 0:
                continue
            t = 1 - life
            txt = self.fonts["small"].render(f"+{amt}", True, UI_GOLD)
            txt.set_alpha(int(255 * life))
            self.screen.blit(txt, (fx - txt.get_width() / 2, fy - 30 * t))
            new_floats.append((amt, fx, fy, life))
        self.floating_texts = new_floats

        # Apply screen shake by re-blitting (cheap implementation)
        if ox or oy:
            shake_layer = self.screen.copy()
            self.screen.fill(BLACK)
            self.screen.blit(shake_layer, (ox, oy))

        # UI overlays
        if self.state == State.TITLE:
            self._draw_title()
        elif self.state == State.PLAYING or self.state == State.DYING:
            self._draw_hud()
        elif self.state == State.LEVEL_COMPLETE:
            self._draw_hud()
            self._draw_level_complete()
        elif self.state == State.GAME_OVER:
            self._draw_hud()
            self._draw_game_over()

    def _draw_backdrop_supports(self):
        # Vertical structural columns
        for cx in (40, WIDTH - 40):
            col = pygame.Rect(cx - 8, 80, 16, HEIGHT - 80)
            pygame.draw.rect(self.screen, (60, 70, 100), col, border_radius=3)
            pygame.draw.rect(self.screen, (40, 50, 80), col, width=2, border_radius=3)
        # Crane silhouette top-left
        pygame.draw.line(self.screen, (50, 60, 90), (40, 80), (260, 60), 6)
        pygame.draw.line(self.screen, (50, 60, 90), (260, 60), (260, 120), 4)
        pygame.draw.rect(self.screen, (50, 60, 90), (250, 120, 22, 12), border_radius=2)

    def _draw_hud(self):
        # Top bar
        bar = pygame.Surface((WIDTH, 56), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 110))
        self.screen.blit(bar, (0, 0))

        # Score
        score_label = self.fonts["small"].render("SCORE", True, UI_DIM)
        score_val = self.fonts["med"].render(f"{self.score:06d}", True, UI_FG)
        self.screen.blit(score_label, (24, 6))
        self.screen.blit(score_val, (24, 18))

        # Level
        lvl_label = self.fonts["small"].render("LEVEL", True, UI_DIM)
        lvl_val = self.fonts["med"].render(f"{self.level_num:02d}", True, UI_ACCENT)
        self.screen.blit(lvl_label, (WIDTH // 2 - 30, 6))
        self.screen.blit(lvl_val, (WIDTH // 2 - 18, 18))

        # High score
        hi_label = self.fonts["small"].render("HIGH", True, UI_DIM)
        hi_val = self.fonts["med"].render(f"{max(self.highscore, self.score):06d}", True, UI_GOLD)
        self.screen.blit(hi_label, (WIDTH - 200, 6))
        self.screen.blit(hi_val, (WIDTH - 200, 18))

        # Lives — small hero icons
        for i in range(self.lives):
            lx = WIDTH - 40 - i * 24
            pygame.draw.circle(self.screen, HERO_HAT, (lx, HEIGHT - 28), 8)
            pygame.draw.circle(self.screen, HERO_BODY, (lx, HEIGHT - 18), 7)
            pygame.draw.circle(self.screen, HERO_BODY_LO, (lx, HEIGHT - 18), 7, 1)

        lives_label = self.fonts["small"].render("LIVES", True, UI_DIM)
        self.screen.blit(lives_label, (WIDTH - 110, HEIGHT - 30))

        # Hammer timer bar
        if self.hero.has_hammer:
            bw = 200
            x = WIDTH // 2 - bw // 2
            y = HEIGHT - 36
            pygame.draw.rect(self.screen, (0, 0, 0, 120), (x - 2, y - 2, bw + 4, 14), border_radius=6)
            t = max(0.0, self.hero.hammer_time / 7.5)
            pygame.draw.rect(self.screen, HAMMER_HEAD, (x, y, int(bw * t), 10), border_radius=4)
            pygame.draw.rect(self.screen, HAMMER_GLOW, (x, y, int(bw * t), 4), border_radius=4)
            label = self.fonts["tiny"].render("HAMMER", True, UI_FG)
            self.screen.blit(label, (x + bw // 2 - label.get_width() // 2, y - 14))

    def _draw_title(self):
        # Subtle scan of accent light
        pulse = 0.5 + 0.5 * math.sin(self.title_blink * 2)
        # Decorative beams for the title
        # Title text
        title = self.fonts["huge"].render(TITLE_TEXT, True, UI_FG)
        shadow = self.fonts["huge"].render(TITLE_TEXT, True, BEAM_LO)
        glow = self.fonts["huge"].render(TITLE_TEXT, True, UI_ACCENT)
        glow.set_alpha(int(120 * pulse))
        tx = WIDTH // 2 - title.get_width() // 2
        ty = 130
        self.screen.blit(shadow, (tx + 6, ty + 6))
        self.screen.blit(title, (tx, ty))
        self.screen.blit(glow, (tx, ty))

        # Sub-title
        sub = self.fonts["med"].render("Climb. Smash. Rescue.", True, UI_DIM)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, ty + 110))

        # Animated ape preview
        self.ape.x = 230
        self.ape.y = 470
        self.ape.draw(self.screen)
        # Damsel preview
        self.damsel.x = 730
        self.damsel.y = 470
        self.damsel.update(0)
        self.damsel.draw(self.screen, self.fonts)
        # A taunting barrel
        bx = 440 + math.sin(self.title_blink * 1.5) * 60
        pygame.draw.ellipse(self.screen, BARREL, (bx - 18, 450, 36, 28))
        pygame.draw.ellipse(self.screen, BARREL_LO, (bx - 18, 450, 36, 28), 2)

        # Start button
        mx, my = pygame.mouse.get_pos()
        hovered = self.start_button.collidepoint(mx, my)
        btn_color = UI_ACCENT if hovered else BEAM
        pygame.draw.rect(self.screen, BLACK, self.start_button.inflate(8, 8), border_radius=14)
        pygame.draw.rect(self.screen, btn_color, self.start_button, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, self.start_button, width=2, border_radius=12)
        btn_text = self.fonts["med"].render("START", True, BLACK if hovered else WHITE)
        self.screen.blit(
            btn_text,
            (
                self.start_button.centerx - btn_text.get_width() // 2,
                self.start_button.centery - btn_text.get_height() // 2,
            ),
        )

        # Press to start
        if int(self.title_blink * 2) % 2 == 0:
            hint = self.fonts["small"].render("Press ENTER or click START", True, UI_FG)
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 140))

        # Controls hint
        controls = self.fonts["tiny"].render(
            "Arrows / WASD = move   |   Space = jump   |   Up/Down = climb ladders   |   Esc = quit",
            True,
            UI_DIM,
        )
        self.screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT - 80))

        # High score
        hi = self.fonts["small"].render(f"HIGH SCORE: {self.highscore:06d}", True, UI_GOLD)
        self.screen.blit(hi, (WIDTH // 2 - hi.get_width() // 2, HEIGHT - 50))

    def _draw_level_complete(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))
        # Title
        msg = self.fonts["big"].render("RESCUED!", True, UI_GOLD)
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 180))
        sub = self.fonts["med"].render("HOW HIGH WILL YOU CLIMB?", True, UI_FG)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 260))
        score_txt = self.fonts["med"].render(f"SCORE: {self.score:06d}", True, UI_ACCENT)
        self.screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 330))
        if int(self.title_blink * 2) % 2 == 0:
            hint = self.fonts["small"].render("Press SPACE to climb higher", True, UI_DIM)
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 410))

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        msg = self.fonts["big"].render("GAME OVER", True, DANGER)
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 200))
        score_txt = self.fonts["med"].render(f"FINAL SCORE: {self.score:06d}", True, UI_FG)
        self.screen.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 290))
        hi_txt = self.fonts["small"].render(f"BEST: {self.highscore:06d}", True, UI_GOLD)
        self.screen.blit(hi_txt, (WIDTH // 2 - hi_txt.get_width() // 2, 340))
        if int(self.title_blink * 2) % 2 == 0:
            hint = self.fonts["small"].render("Press SPACE to return to title", True, UI_DIM)
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 410))


# ============================================================
#  ENTRY POINT
# ============================================================
def main():
    game = ApeEscape()
    game.run()


if __name__ == "__main__":
    main()
