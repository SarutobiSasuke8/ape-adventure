"""In-game pause menu: resume, restart, settings, quit to title.

Pure menu logic plus a draw method. The owning gameplay state feeds it input
snapshots and acts on the action string ``handle`` returns.
"""
from __future__ import annotations

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot
from ape_escape.data.settings import Settings

RESUME = "resume"
RESTART = "restart"
QUIT_TO_TITLE = "quit_to_title"
SETTINGS_CHANGED = "settings_changed"

MAIN_ITEMS = ("Resume", "Restart", "Settings", "Quit to title")
SETTINGS_ITEMS = ("Music volume", "SFX volume", "Reduced motion", "Back")


class PauseMenu:
    """Two-page menu. ``page`` is "main" or "settings"."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.page = "main"
        self.index = 0
        self._fonts: tuple[pygame.font.Font, ...] | None = None

    def reset(self) -> None:
        self.page = "main"
        self.index = 0

    @property
    def items(self) -> tuple[str, ...]:
        return MAIN_ITEMS if self.page == "main" else SETTINGS_ITEMS

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle(self, snap: InputSnapshot) -> str | None:
        """Process one frame of input. Returns an action string or None."""
        if snap.up:
            self.index = (self.index - 1) % len(self.items)
        if snap.down:
            self.index = (self.index + 1) % len(self.items)

        if self.page == "main":
            return self._handle_main(snap)
        return self._handle_settings(snap)

    def _handle_main(self, snap: InputSnapshot) -> str | None:
        if snap.pause:
            return RESUME
        if snap.confirm or snap.jump:
            choice = MAIN_ITEMS[self.index]
            if choice == "Resume":
                return RESUME
            if choice == "Restart":
                return RESTART
            if choice == "Settings":
                self.page = "settings"
                self.index = 0
                return None
            if choice == "Quit to title":
                return QUIT_TO_TITLE
        return None

    def _handle_settings(self, snap: InputSnapshot) -> str | None:
        if snap.pause:
            self._back_to_main()
            return None
        choice = SETTINGS_ITEMS[self.index]
        step = (1 if snap.right else 0) - (1 if snap.left else 0)
        activate = snap.confirm or snap.jump
        changed = False
        if choice == "Music volume" and step:
            self.settings.adjust_music(step)
            changed = True
        elif choice == "SFX volume" and step:
            self.settings.adjust_sfx(step)
            changed = True
        elif choice == "Reduced motion" and (step or activate):
            self.settings.toggle_reduced_motion()
            changed = True
        elif choice == "Back" and activate:
            self._back_to_main()
        if changed:
            self.settings.save()
            return SETTINGS_CHANGED
        return None

    def _back_to_main(self) -> None:
        self.page = "main"
        self.index = MAIN_ITEMS.index("Settings")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _value_label(self, item: str) -> str:
        s = self.settings
        if item == "Music volume":
            return f"< {round(s.music_volume * 100)}% >"
        if item == "SFX volume":
            return f"< {round(s.sfx_volume * 100)}% >"
        if item == "Reduced motion":
            return "< On >" if s.reduced_motion else "< Off >"
        return ""

    def draw(self, surf: pygame.Surface) -> None:
        if self._fonts is None:
            self._fonts = (
                pygame.font.SysFont("arial", 52, bold=True),
                pygame.font.SysFont("arial", 28, bold=True),
                pygame.font.SysFont("arial", 18),
            )
        f_title, f_item, f_hint = self._fonts
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        surf.blit(ov, (0, 0))

        title_text = "PAUSED" if self.page == "main" else "SETTINGS"
        title = f_title.render(title_text, True, (250, 210, 90))
        surf.blit(title, title.get_rect(center=(w // 2, 110)))

        top = 190
        for i, item in enumerate(self.items):
            selected = i == self.index
            col = (255, 235, 140) if selected else (190, 220, 170)
            y = top + i * 48
            if selected:
                bar = pygame.Rect(0, 0, 460, 40)
                bar.center = (w // 2, y)
                pygame.draw.rect(surf, (60, 90, 40), bar, border_radius=8)
                pygame.draw.rect(surf, (250, 210, 90), bar, 2, border_radius=8)
            label = f_item.render(item, True, col)
            value = self._value_label(item)
            if value:
                surf.blit(label, label.get_rect(midleft=(w // 2 - 210, y)))
                vt = f_item.render(value, True, col)
                surf.blit(vt, vt.get_rect(midright=(w // 2 + 210, y)))
            else:
                surf.blit(label, label.get_rect(center=(w // 2, y)))

        if self.page == "main":
            hint_text = "Up / Down: choose    Enter / Space: select    Esc / P: resume"
        else:
            hint_text = "Up / Down: choose    Left / Right: change    Esc / P: back"
        hint = f_hint.render(hint_text, True, (170, 200, 150))
        surf.blit(hint, hint.get_rect(center=(w // 2, h - 40)))
