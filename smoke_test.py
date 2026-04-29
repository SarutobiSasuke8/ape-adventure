"""Headless smoke test — runs the game for ~3 seconds with simulated input."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import sys
import pygame
import ape_escape as g

pygame.init()
pygame.display.set_mode((g.WIDTH, g.HEIGHT))

game = g.ApeEscape()
print("Init OK")

# Force into PLAYING state
game.state = g.State.PLAYING

# Simulate frames
frames = 240  # 4 seconds at 60fps
errors = []

class FakeKeys:
    def __init__(self, pressed):
        self.pressed = set(pressed)
    def __getitem__(self, k):
        return k in self.pressed

# Patch key state for the test
import builtins
orig_get_pressed = pygame.key.get_pressed

# Sequence: walk right 60f, jump+right 60f, climb up 60f, idle 60f
def keys_for_frame(f):
    if f < 60:
        return FakeKeys([pygame.K_RIGHT])
    if f < 120:
        return FakeKeys([pygame.K_RIGHT, pygame.K_SPACE])
    if f < 180:
        return FakeKeys([pygame.K_UP])
    return FakeKeys([])

current_frame = [0]
def fake_get_pressed():
    return keys_for_frame(current_frame[0])

pygame.key.get_pressed = fake_get_pressed

try:
    for f in range(frames):
        current_frame[0] = f
        # pump events so pygame is happy
        pygame.event.pump()
        game._update(1 / 60.0)
        game._draw()
    print(f"Simulated {frames} frames OK")
    print(f"Hero position: ({game.hero.x:.0f}, {game.hero.y:.0f})")
    print(f"Hero alive: {game.hero.alive}")
    print(f"Lives: {game.lives}")
    print(f"Score: {game.score}")
    print(f"Barrels active: {len(game.barrels)}")
    print(f"State: {game.state.name}")
except Exception as e:
    import traceback
    traceback.print_exc()
    errors.append(str(e))

pygame.quit()
sys.exit(1 if errors else 0)
