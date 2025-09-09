from arcade import Vec2
from arcade.types import Point2

from jam2025.core.game.lux import PlayerRenderer, LuxRenderer

class Character:
    def __init__(self) -> None:
        self.position: Vec2 = Vec2()
        self.velocity: Vec2 = Vec2()
        self.size: float = 20
        self.health: float = 5

        # self.renderer = PlayerRenderer()
        self.renderer = LuxRenderer()

    def reset(self):
        self.position = Vec2()
        self.velocity = Vec2()
        self.size = 20
        self.health = 5

        self.renderer.reset()

    def update(self, delta_time: float, position: Vec2 | None = None) -> None:
        if position is not None:
            dx = (position[0] - self.position[0]) / delta_time
            dy = (position[1] - self.position[1]) / delta_time
            self.velocity = Vec2(dx, dy)
            self.position = position
        self.renderer.position = self.position
        self.renderer.velocity = self.velocity
        self.renderer.update(delta_time)

    def draw(self) -> None:
        self.renderer.draw()
