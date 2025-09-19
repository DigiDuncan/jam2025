from arcade import SpriteList, TextureAnimationSprite, Vec2
import arcade
from arcade.types import Color
from arcade.clock import GLOBAL_CLOCK
from jam2025.core.game.bullet import BulletEmitter
from jam2025.core.game.lux import LuxRenderer
from jam2025.core.settings import settings
from jam2025.lib.utils import draw_cross

from jam2025.data.loading import load_spritesheet

bullet_sprite = load_spritesheet("energy_ball", 1, 30, 30, 30)

class Enemy:
    def __init__(self, color: Color, emitter: BulletEmitter) -> None:
        self._position: Vec2 = Vec2()
        self.velocity: Vec2 = Vec2()
        self.size: float = 10
        self.emitter = emitter
        self.emitter.sprite.position = self._position

        self.renderer = LuxRenderer(color, self.size)

        self.live = True

    @property
    def position(self) -> Vec2:
        return self._position

    @position.setter
    def position(self, v: Vec2) -> None:
        delta_time = GLOBAL_CLOCK.delta_time
        dx = (v[0] - self.position[0]) / delta_time
        dy = (v[1] - self.position[1]) / delta_time
        self.velocity = Vec2(dx, dy)
        self._position = v
        self.emitter.sprite.position = v
        self.renderer.position = self.position
        self.renderer.velocity = self.velocity
        self.renderer.update(delta_time)

    def draw(self) -> None:
        self.renderer.draw()
        if settings.debug:
            self.debug_draw()

    def debug_draw(self) -> None:
        arcade.draw_circle_outline(*self.position, self.size, arcade.color.RED, 3)
        draw_cross(Vec2(*self.emitter.sprite.position), self.size, arcade.color.GREEN)


class BossEnemy(Enemy):
    def __init__(self, emitter: BulletEmitter) -> None:
        self.sprite = TextureAnimationSprite()
        self.sprite.textures = bullet_sprite.textures
        self.sprite.animation = bullet_sprite.animation
        self.size: float = 128
        self.sprite.width = self.size
        self.sprite.height = self.size
        self.velocity: Vec2 = Vec2()
        self.emitter = emitter
        self.emitter.sprite.position = self.sprite.position

        self.sprite_list = SpriteList()
        self.sprite_list.append(self.sprite)

        self.live = True

    @property
    def position(self) -> Vec2:
        return Vec2(*self.sprite.position)

    @position.setter
    def position(self, v: Vec2) -> None:
        self.sprite.position = v
        self.emitter.sprite.position = v

    def draw(self) -> None:
        self.sprite_list.draw()
        if settings.debug:
            self.debug_draw()

    def debug_draw(self) -> None:
        arcade.draw_circle_outline(*self.position, self.size, arcade.color.RED, 3)
