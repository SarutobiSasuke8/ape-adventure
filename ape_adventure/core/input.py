"""Input layer. Reads pygame events into a structured per-frame snapshot."""
from __future__ import annotations

from dataclasses import dataclass
import pygame


@dataclass(frozen=True)
class InputSnapshot:
    move_x: float = 0.0          # -1, 0, +1
    jump: bool = False           # pressed this frame
    jump_held: bool = False      # currently held (for variable-height jump)
    run: bool = False            # held
    roll: bool = False           # pressed this frame
    confirm: bool = False        # menu accept (pressed)
    cancel: bool = False         # menu back (pressed)
    start: bool = False          # pause / start (pressed)
    quit: bool = False           # esc on title screen


class Input:
    """Translates raw pygame keys into the snapshot the game logic consumes."""

    def __init__(self) -> None:
        self._prev_keys = pygame.key.ScancodeWrapper() if False else None

    def poll(self, events) -> InputSnapshot:
        keys = pygame.key.get_pressed()

        # Edge-triggered presses come from event stream.
        jump_pressed = False
        roll_pressed = False
        confirm_pressed = False
        cancel_pressed = False
        start_pressed = False
        quit_pressed = False
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_z):
                    jump_pressed = True
                if ev.key in (pygame.K_LSHIFT, pygame.K_x):
                    roll_pressed = True
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    confirm_pressed = True
                if ev.key == pygame.K_ESCAPE:
                    cancel_pressed = True
                    quit_pressed = True
                if ev.key in (pygame.K_p, pygame.K_RETURN):
                    start_pressed = True

        move_x = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += 1.0

        return InputSnapshot(
            move_x=move_x,
            jump=jump_pressed,
            jump_held=keys[pygame.K_SPACE] or keys[pygame.K_z],
            run=keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT],
            roll=roll_pressed,
            confirm=confirm_pressed,
            cancel=cancel_pressed,
            start=start_pressed,
            quit=quit_pressed,
        )
