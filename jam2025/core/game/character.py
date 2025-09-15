from arcade import Vec2
import arcade

from jam2025.core.game.lux import LuxRenderer
from jam2025.core.settings import settings

class Character:
    def __init__(self) -> None:
        self.position: Vec2 = Vec2()
        self.velocity: Vec2 = Vec2()
        self.size: float = 20
        self.health: float = 5
        self.max_health: float = 5

        # self.renderer = PlayerRenderer()
        self.renderer = LuxRenderer()

        self.invincibility_time = 1.0
        self._invicibility_timer = self.invincibility_time

    @property
    def invincible(self) -> bool:
        return bool(self._invicibility_timer)

    def iframes(self) -> None:
        self._invicibility_timer = self.invincibility_time

    def reset(self) -> None:
        self.position = Vec2()
        self.velocity = Vec2()
        self.size = 20
        self.health = self.max_health
        self._invicibility_timer = self.invincibility_time

        self.renderer.reset()

    def update(self, delta_time: float, position: Vec2 | None = None) -> None:
        self._invicibility_timer -= delta_time
        self._invicibility_timer = max(self._invicibility_timer, 0)
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
        if settings.debug:
            self.debug_draw()

    def debug_draw(self) -> None:
        arcade.draw_circle_outline(*self.position, self.size, arcade.color.RED if not self._invicibility_timer else arcade.color.YELLOW, 3)
