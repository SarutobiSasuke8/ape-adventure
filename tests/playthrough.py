"""Scripted playthroughs: prove each Tangle Jungle level can be finished.

Each level has an input script (a generator of ``InputSnapshot``) that reads
the live game state, the way a player reacts to what is on screen. The script
drives the real ``LevelState`` (real physics, enemies, vines, boss, goal
totem) at a fixed 60 fps step. A run passes only if the player touches the
goal totem and the state machine moves to ``ResultsState`` without dying.

``play_world`` chains the whole of World 1 (1-1 to 1-4) the way a player
does, following each ``ResultsState`` into the next level, and records the
checkpoints reached and the King Saurus coconut volleys dodged on the way.

Audio is replaced by a silent stub, so no music thread is started.

Usage (from the repo root):

    python -m tests.playthrough            # chain 1-1 to 1-4, print a summary
    python -m tests.playthrough 1-2 --trace  # one level, position trace
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Iterator
from unittest import mock

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ape_escape.core import constants as C
from ape_escape.core.input import InputSnapshot as S

DT = 1.0 / C.FPS
TILE = C.TILE_SIZE


class SilentAudio:
    """Stand-in for AudioManager: same surface, no mixer, no music thread."""

    def __init__(self, music_key: str = "") -> None:
        self.music_key = music_key
        self.played: list[str] = []

    def set_volumes(self, music: float, sfx: float) -> None: ...
    def set_ducked(self, ducked: bool) -> None: ...
    def poll_music(self) -> None: ...
    def stop_music(self) -> None: ...
    def shutdown(self) -> None: ...

    def play(self, key: str) -> None:
        self.played.append(key)


class MemorySave:
    def __init__(self) -> None:
        self.cleared: list[str] = []

    def record_clear(self, level_id, time, bananas, aape) -> dict[str, bool]:
        self.cleared.append(level_id)
        return {"new_time": True, "new_bananas": True, "new_aape": True}

    def best_time(self, level_id):
        return None


class HarnessGame:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.next_state = None
        self.running = True
        self.save = MemorySave()

    def change_state(self, new_state) -> None:
        self.next_state = new_state


def make_level_state(game: HarnessGame, level_index: int):
    from ape_escape.core.states import LevelState

    state = LevelState(game, level_index)
    with mock.patch("ape_escape.audio.audio.AudioManager", SilentAudio):
        state.enter()
    return state


# ---------------------------------------------------------------------------
# Script building blocks. Each is a generator of input snapshots that reads
# the live LevelState `st`.
# ---------------------------------------------------------------------------

Script = Iterator[S]


def cx(st) -> float:
    return st.player.rect.centerx


def _harmful_enemy_ahead(st, reach: float) -> bool:
    from ape_escape.entities.enemies.enemy import Enemy

    pr = st.player.rect
    for e in st.level.entities:
        if not isinstance(e, Enemy) or not e.harmful:
            continue
        dx = e.rect.centerx - pr.centerx
        same_level = -100 < e.rect.bottom - pr.bottom < 40  # hoppers read from mid-hop
        if same_level and 0 < dx < reach:
            return True
    return False


def _low_ceiling(st) -> bool:
    """True if a jump from here would bonk within about 1.5 tiles."""
    p = st.player
    tg = st.level.tile_grid
    head_row = (p.rect.top - 1) // TILE
    cols = {p.rect.left // TILE, (p.rect.right - 1) // TILE, (p.rect.right + 40) // TILE}
    return any(tg.get(c, r) for c in cols for r in (head_row, head_row - 1))


def run_to(st, x: float, *, run: bool = True, hop_enemies: bool = True,
           attack: str = "jump") -> Script:
    """Run right until the player's centre reaches *x*. Deals with enemies in
    the way: jump on or over them (attack="jump"), or roll into them
    (attack="roll", and always under a low ceiling)."""
    while cx(st) < x:
        p = st.player
        if hop_enemies and p.on_ground and p.rolling_timer <= 0:
            if attack == "roll" and _harmful_enemy_ahead(st, 110):
                yield S(move_x=1.0, run=run, roll=True)
                continue
            if _low_ceiling(st) and _harmful_enemy_ahead(st, 70):
                yield S(move_x=1.0, run=run, roll=True)
                continue
            if not _low_ceiling(st) and _harmful_enemy_ahead(st, 90):
                yield from jump(st, hold=26)
                continue
        yield S(move_x=1.0, run=run, jump_held=True)


def walk_to(st, x: float) -> Script:
    """Walk (either direction) until the player's centre is within 4 px of *x*."""
    while abs(cx(st) - x) > 4:
        yield S(move_x=1.0 if x > cx(st) else -1.0)
    for _ in range(10):
        yield S()


def jump(st, hold: int = 30, move_x: float = 1.0) -> Script:
    """Press jump, hold it for *hold* frames, then keep steering until grounded."""
    yield S(move_x=move_x, run=True, jump=True, jump_held=True)
    for _ in range(hold):
        yield S(move_x=move_x, run=True, jump_held=True)
    yield from land(st, move_x)


def land(st, move_x: float = 1.0) -> Script:
    while not st.player.on_ground and st.player.vine is None:
        yield S(move_x=move_x, run=True, jump_held=True)


def jump_at(st, x: float, hold: int = 30, attack: str = "jump") -> Script:
    yield from run_to(st, x, attack=attack)
    yield from land(st)
    yield from jump(st, hold)


def vine_swing(st, take_off_x: float, release_theta: float) -> Script:
    """Jump from *take_off_x* into the next vine, pump, and let go on the
    forward swing once the angle passes *release_theta* (radians)."""
    yield from run_to(st, take_off_x - 150)
    yield from land(st)
    yield from run_to(st, take_off_x, hop_enemies=False)
    yield S(move_x=1.0, run=True, jump=True, jump_held=True)
    yield from swing_from_air(st, release_theta)


def swing_from_air(st, release_theta: float) -> Script:
    p = st.player
    frames = 0
    while p.vine is None:
        if p.on_ground and frames > 2:
            raise ScriptError(f"missed the vine, landed at x={cx(st):.0f}")
        frames += 1
        yield S(move_x=1.0, run=True, jump_held=True)
    while not (p.swing_theta >= release_theta and p.swing_omega > 0):
        yield S(move_x=1.0 if p.swing_omega >= 0 else -1.0)
    yield S(move_x=1.0, jump=True, jump_held=True)
    for _ in range(4):
        yield S(move_x=1.0, run=True, jump_held=True)


def roll_through(st, x_end: float) -> Script:
    """Roll and keep rolling (or crawling) right until past *x_end* and standing."""
    p = st.player
    while cx(st) < x_end or p.crouched:
        if p.rolling_timer <= 0:
            yield S(move_x=1.0, roll=True)
        else:
            yield S(move_x=1.0)


def wait_until(st, cond: Callable[[], bool], limit: int = 600, hold: S | None = None) -> Script:
    for _ in range(limit):
        if cond():
            return
        yield hold or S()
    raise ScriptError("wait_until timed out")


class ScriptError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Level scripts
# ---------------------------------------------------------------------------

def script_1_1(st) -> Script:
    yield from jump_at(st, 32 * TILE)          # pit 1 (cols 34-36)
    yield from jump_at(st, 68 * TILE)          # pit 2 (cols 70-72)
    yield from run_to(st, 107 * TILE)


def script_1_2(st) -> Script:
    yield from vine_swing(st, 16 * TILE - 16, 0.80)   # gap A (cols 16-23)
    yield from land(st)
    yield from vine_swing(st, 40 * TILE - 16, 0.80)   # gap B (cols 40-47)
    yield from land(st)
    yield from jump_at(st, 55 * TILE)                 # small pit (cols 56-58)
    yield from vine_swing(st, 64 * TILE - 16, 0.45)   # gap C (cols 64-77), first vine
    yield from swing_from_air(st, 0.80)               # gap C, second vine
    yield from land(st)
    yield from vine_swing(st, 96 * TILE - 16, 0.80)   # gap D (cols 96-103)
    yield from land(st)
    yield from run_to(st, 126 * TILE)


def script_1_3(st) -> Script:
    R = "roll"  # this level's answer to enemies on the ground is the roll attack
    yield from run_to(st, 12 * TILE, attack=R)
    yield from roll_through(st, 21 * TILE)            # log 1 (cols 14-19)
    yield from jump_at(st, 29 * TILE + 8, attack=R)   # pit (cols 30-33)
    yield from run_to(st, 36 * TILE, attack=R)
    yield from roll_through(st, 49 * TILE)            # log 2 (cols 38-47), Snapper inside
    yield from jump_at(st, 59 * TILE + 8, attack=R)   # pit (cols 60-63)
    yield from jump_at(st, 65 * TILE, hold=20)        # onto the step block (cols 66-67)
    yield from run_to(st, 68 * TILE + 16)             # drop off it
    yield from land(st)
    yield from roll_through(st, 81 * TILE)            # log 3 tunnel (cols 70-79)
    yield from run_to(st, 92 * TILE, attack=R)
    yield from roll_through(st, 107 * TILE)           # log 4 (cols 94-105), two Snappers
    yield from jump_at(st, 109 * TILE + 8, attack=R)  # pit (cols 110-113)
    yield from run_to(st, 135 * TILE, attack=R)


def live_coconuts(st) -> list:
    from ape_escape.entities.hazards.coconut import Coconut

    return [e for e in st.level.entities if isinstance(e, Coconut) and e.state in ("warn", "fall")]


def coconut_threat(st, x: float, margin: float = 10.0) -> bool:
    """True if a coconut still to land would hit a player centred at *x*."""
    half = st.player.rect.width / 2 + margin
    return any(abs(c.rect.centerx - x) < half + c.rect.width / 2 for c in live_coconuts(st))


def hold_ledge_dodging(st, ledge_x: float, lo: float, hi: float, until: Callable[[], bool],
                       limit: int = 900) -> Script:
    """Stand near *ledge_x* until *until()*; step out of any coconut shadow
    (staying between *lo* and *hi*) and come back once it has landed."""
    for _ in range(limit):
        if until():
            return
        if coconut_threat(st, ledge_x):
            # Nearest safe spot along the ledge / corridor.
            options = [x for x in range(int(lo), int(hi) + 1, 4) if not coconut_threat(st, x)]
            goal = min(options, key=lambda x: abs(x - cx(st))) if options else lo
        else:
            goal = ledge_x
        dx = goal - cx(st)
        yield S(move_x=0.0 if abs(dx) <= 3 else (1.0 if dx > 0 else -1.0), run=abs(dx) > 40)
    raise ScriptError("hold_ledge_dodging timed out")


def script_1_4(st) -> Script:
    from ape_escape.entities.enemies.king_saurus import KingSaurus

    boss = next(e for e in st.level.entities if isinstance(e, KingSaurus))
    arena = boss.arena_left or 0.0
    ledge_x = arena + 2 * TILE + TILE / 2      # middle of the left safe ledge
    ledge_face = arena + 4 * TILE              # where he crashes
    # Approach corridor: Snapper, stump, then the arena-gate checkpoint.
    yield from jump_at(st, arena - 4 * TILE, hold=20)
    yield from run_to(st, ledge_x - 24)
    yield from land(st)
    yield from walk_to(st, ledge_x)
    for _ in range(3):
        # Wait on the left ledge for him to crash into it, dodging coconuts.
        yield from hold_ledge_dodging(
            st, ledge_x, lo=arena - 6 * TILE, hi=ledge_face - 20,
            until=lambda: (boss.state == "dazed" and not live_coconuts(st)) or not boss.alive)
        # Hop off the ledge onto his head.
        yield S(move_x=1.0, jump=True, jump_held=True)
        hit_hp = boss.hp
        for _ in range(90):
            if boss.hp < hit_hp:
                break
            yield S(move_x=1.0 if cx(st) < boss.rect.centerx else 0.0, jump_held=True)
        if boss.hp >= hit_hp:
            raise ScriptError("stomp missed")
        if boss.hp <= 0:
            break
        # Bounce back onto the ledge before his next charge.
        while not (st.player.on_ground and cx(st) < ledge_face):
            yield S(move_x=-1.0, jump_held=True,
                    jump=st.player.on_ground)
        yield from walk_to(st, ledge_x)
    yield from wait_until(st, lambda: not boss.alive, limit=300)
    from ape_escape.entities.collectibles.goal_totem import GoalTotem

    totem = next(e for e in st.level.entities if isinstance(e, GoalTotem))
    yield from wait_until(st, lambda: not totem.locked, limit=60)
    yield from jump(st, hold=20)                       # off the ledge
    while st.game.next_state is None:
        yield S(move_x=1.0 if cx(st) < totem.rect.centerx else -1.0)


SCRIPTS: dict[str, Callable] = {
    "1-1": script_1_1,
    "1-2": script_1_2,
    "1-3": script_1_3,
    "1-4": script_1_4,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    level_id: str
    completed: bool
    frames: int
    hits_taken: int
    deaths: int
    bananas: int
    total_bananas: int
    letters: int
    error: str = ""
    trace: list[str] = field(default_factory=list)
    checkpoints: int = 0           # checkpoints reached
    coconut_volleys: int = 0       # King Saurus coconut volleys thrown
    coconuts: int = 0              # coconuts dropped in those volleys

    @property
    def seconds(self) -> float:
        return self.frames * DT

    def summary(self) -> str:
        status = "COMPLETED" if self.completed else f"FAILED ({self.error})"
        extra = f", checkpoints {self.checkpoints}"
        if self.coconut_volleys:
            extra += f", coconut volleys {self.coconut_volleys} ({self.coconuts} coconuts)"
        return (f"{self.level_id}: {status} in {self.seconds:.1f}s game time, "
                f"hits {self.hits_taken}, deaths {self.deaths}, "
                f"bananas {self.bananas}/{self.total_bananas}, letters {self.letters}/4{extra}")


def play_level(level_index: int, *, max_seconds: float = 180.0, trace: bool = False,
               draw_every: int = 15, game: HarnessGame | None = None) -> RunResult:
    """Run one level's script to the goal. Assumes pygame is initialised.

    Pass *game* to keep playing in an existing harness (see ``play_world``)."""
    from ape_escape.core.states import ResultsState
    from ape_escape.entities.enemies.king_saurus import KingSaurus
    from ape_escape.entities.hazards.coconut import Coconut
    from ape_escape.levels.world_data import ALL_WORLDS

    entry = ALL_WORLDS[0].levels[level_index]
    screen = pygame.display.get_surface() or pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
    if game is None:
        game = HarnessGame(screen)
    game.next_state = None
    st = make_level_state(game, level_index)
    boss = next((e for e in st.level.entities if isinstance(e, KingSaurus)), None)
    coconuts_seen: set[int] = set()
    assert st.level.level_id == entry.id, f"loaded {st.level.level_id!r}, expected {entry.id!r}"

    script = SCRIPTS[entry.id](st)
    frames = hits = deaths = 0
    last_health = st.player.health
    was_dead = False
    lines: list[str] = []
    error = ""
    try:
        while frames < int(max_seconds * C.FPS):
            try:
                snap = next(script)
            except StopIteration:
                snap = S()
            st.handle(snap)
            st.update(DT)
            if draw_every and frames % draw_every == 0:
                st.draw(screen)
            frames += 1
            if boss is not None:
                coconuts_seen.update(id(e) for e in st.level.entities if isinstance(e, Coconut))
            p = st.player
            if p.health < last_health and not p.dead:
                hits += 1
            last_health = p.health
            if p.dead and not was_dead:
                deaths += 1
                error = f"died at x={p.rect.centerx}, y={p.rect.bottom}"
                break
            was_dead = p.dead
            if trace and frames % 10 == 0:
                lines.append(
                    f"f{frames:5d} x={p.rect.centerx:5d} ({p.rect.centerx / TILE:5.1f}) "
                    f"y={p.rect.bottom:4d} {p.state:6s} hp={p.health} "
                    f"vine={'Y' if p.vine else '-'} th={p.swing_theta:+.2f}"
                )
            if isinstance(game.next_state, ResultsState):
                break
        else:
            error = error or f"timed out at x={st.player.rect.centerx}"
    except ScriptError as exc:
        error = str(exc)
    finally:
        st.exit()

    completed = isinstance(game.next_state, ResultsState) and deaths == 0
    if completed:
        assert game.next_state.results["level_id"] == entry.id
    return RunResult(
        level_id=entry.id,
        completed=completed,
        frames=frames,
        hits_taken=hits,
        deaths=deaths,
        bananas=st.banana_count,
        total_bananas=st.level.total_bananas,
        letters=len(st.aape_collected),
        error=error if not completed else "",
        trace=lines,
        checkpoints=sum(1 for c in st.level.checkpoints() if c.active),
        coconut_volleys=boss.volleys if boss is not None else 0,
        coconuts=len(coconuts_seen),
    )


def play_world(**kwargs) -> list[RunResult]:
    """Play World 1 end to end: 1-1, then follow each ResultsState's ENTER
    into the next level, until the world-clear screen returns to the title.
    Stops at the first level that is not cleared. Assumes pygame is initialised."""
    from ape_escape.core.states import LevelState, ResultsState, TitleState

    screen = pygame.display.get_surface() or pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
    game = HarnessGame(screen)
    results: list[RunResult] = []
    index = 0
    while True:
        res = play_level(index, game=game, **kwargs)
        results.append(res)
        if not res.completed:
            break
        screen_state = game.next_state
        assert isinstance(screen_state, ResultsState), screen_state
        screen_state.draw(screen)
        game.next_state = None
        screen_state.handle(S(confirm=True))
        if isinstance(game.next_state, TitleState):
            break
        assert isinstance(game.next_state, LevelState), game.next_state
        index = game.next_state.level_index
    return results


def main(argv: list[str]) -> int:
    from ape_escape.levels.world_data import ALL_WORLDS

    trace = "--trace" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    ids = [lv.id for lv in ALL_WORLDS[0].levels]
    pygame.init()
    pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
    ok = True
    try:
        if not wanted:
            results = play_world(trace=trace)
            for res in results:
                if trace:
                    print("\n".join(res.trace))
                print(res.summary())
            ok = [r.level_id for r in results] == ids and all(r.completed for r in results)
            print(f"World 1 chain {'CLEARED' if ok else 'NOT CLEARED'}: "
                  f"{' -> '.join(r.level_id for r in results)}")
        for i, level_id in enumerate(ids):
            if level_id not in wanted:
                continue
            res = play_level(i, trace=trace)
            if trace:
                print("\n".join(res.trace))
            print(res.summary())
            ok = ok and res.completed
    finally:
        pygame.quit()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
