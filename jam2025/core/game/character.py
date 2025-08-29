from arcade import Vec2
from arcade.types import Point2

from jam2025.core.game.lux import LuxSimplified


class Character:
    def __init__(self) -> None:
        self.position = Vec2(0, 0)
        self.size: float = 20
        self.health: float = 100

        self._velocity: Point2 = (0, 0)
        self._direction: Point2 = (1, 0)

        self.renderer = LuxSimplified(self.position)

    @property
    def velocity(self) -> Point2:
        return self._velocity

    def update(self, delta_time: float, position: Point2 | None = None) -> None:
        if position is not None:
            vel = (position[0] - self.position[0]) * delta_time, (position[1] - self.position[1]) * delta_time
            length = (vel[0]**2 + vel[1]**2)**0.5
            self.position = position
            self._velocity = vel
            if length != 0.0:
                self._direction = vel[0]/length, vel[1]/length
        self.renderer.update(delta_time, self.position, self._direction)

    def draw(self) -> None:
        self.renderer.draw()
