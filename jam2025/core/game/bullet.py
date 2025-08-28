from arcade import SpriteCircle, SpriteList
from arcade.clock import GLOBAL_CLOCK
from arcade.types import Point2
import arcade

from jam2025.core.game.character import Character
from jam2025.lib.utils import point_in_circle

class Bullet:
    def __init__(self, radius: float = 10, damage: float = 1, live_time: float = 10) -> None:
        self.sprite = SpriteCircle(radius, arcade.color.RED)  #type: ignore -- float -> int
        self.velocity: Point2 = (0, 0)
        self.damage = damage
        self.live = True
        self.live_time = live_time

        self._creation_time = GLOBAL_CLOCK.time

    def collide(self, character: Character) -> None:
        if point_in_circle(character.position, character.size / 2, self.sprite.position) and self.live:
            character.health -= self.damage
            self.live = False

    def update(self, delta_time: float) -> None:
        """Override this for non-straight bullets."""

        dx = self.velocity[0] * delta_time
        dy = self.velocity[1] * delta_time
        self.sprite.position = (self.sprite.position[0] + dx, self.sprite.position[1] + dy)

        if self._creation_time + self.live_time < GLOBAL_CLOCK.time:
            self.live = False

    def draw(self) -> None:
        ...

class BulletList:
    def __init__(self, bullets: list[Bullet] | None = None) -> None:
        self.bullets = bullets if bullets else []
        self.sprite_list = SpriteList()

    def spawn_bullet(self, bullet_type: type[Bullet], velocity: Point2 = (0, 0)) -> None:
        new_bullet = bullet_type()
        new_bullet.velocity = velocity
        self.bullets.append(new_bullet)
        self.sprite_list.append(new_bullet.sprite)

    def update(self, delta_time: float) -> None:
        for bullet in self.bullets:
            bullet.update(delta_time)

        for bullet in [b for b in self.bullets if not b.live]:
            self.bullets.remove(bullet)
            self.sprite_list.remove(bullet.sprite)

    def draw(self) -> None:
        self.sprite_list.draw()
        for bullet in self.bullets:
            bullet.draw()
