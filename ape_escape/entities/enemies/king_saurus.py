"""King Saurus — World 1 boss. Three-phase fight."""
from ape_escape.entities.enemies.enemy import Enemy


class KingSaurus(Enemy):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, w=72, h=80, hp=3)
        self.phase = 1  # 1=charge, 2=coconut bombs, 3=stage hazard
        self.phase_timer = 0.0
