from arcade import Vec2
from arcade.types import Point2

from jam2025.core.game.lux import PlayerRenderer


class Character:
    def __init__(self) -> None:
        self.position = Vec2(0, 0)
        self.size: float = 20
        self.health: float = 100

        self._velocity: Point2 = (0, 0)

        self.renderer = PlayerRenderer(self)

    @property
    def velocity(self) -> Point2:
        return self._velocity

    def update(self, delta_time: float, position: Point2 | None = None) -> None:
        self.renderer.update(delta_time)
        if position is not None:
            vel = (position[0] - self.position[0]) * delta_time, (position[1] - self.position[1]) * delta_time
            self.position = position
            self._velocity = vel

    def draw(self) -> None:
        self.renderer.draw()
