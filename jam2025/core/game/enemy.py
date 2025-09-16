from arcade import Sprite
from arcade.types import Point2
from jam2025.core.game.bullet import BulletEmitter


class Enemy:
    def __init__(self, sprite: Sprite, emitter: BulletEmitter) -> None:
        self.sprite = sprite
        self.emitter = emitter

        self.live = True

    @property
    def position(self) -> Point2:
        return self.sprite.position

    @position.setter
    def position(self, v: Point2) -> None:
        self.sprite.position = v
