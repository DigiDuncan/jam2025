from typing import Protocol

from arcade import SpriteCircle
from arcade.clock import GLOBAL_CLOCK
from arcade.types import Point2
import arcade

from jam2025.lib.utils import point_in_circle

# !!! TEMPORARY
class Character(Protocol):
    position: Point2
    size: float  # The character is a circle
    health: float


class Bullet:
    def __init__(self, radius: float = 10, damage: float = 1, live_time: float = 10) -> None:
        self.sprite = SpriteCircle(radius, arcade.color.RED)  #type: ignore -- float -> int
        self.velocity = (0, 0)
        self.damage = damage
        self.live = True
        self.live_time = live_time

        self.creation_time = GLOBAL_CLOCK.time

    def collide(self, character: Character) -> None:
        if point_in_circle(character.position, character.size / 2, self.sprite.position) and self.live:
            character.health -= self.damage
            self.live = False

    def update(self, delta_time: float) -> None:
        """Override this for non-straight bullets."""

        dx = self.velocity[0] * delta_time
        dy = self.velocity[1] * delta_time
        self.sprite.position = (self.sprite.position[0] + dx, self.sprite.position[1] + dy)

        if self.creation_time + self.live_time < GLOBAL_CLOCK.time:
            self.live = False

    def draw(self) -> None:
        ...
