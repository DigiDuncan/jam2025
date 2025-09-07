import math
from random import random
from arcade import Vec2, View
from jam2025.core.game.bullet import PATTERNS, BulletEmitter, BulletList, Bullet, RainbowBullet
from jam2025.core.game.character import Character
from jam2025.core.void import Void
from jam2025.data.loading import load_music


class PlayerTestView(View):
    def __init__(self) -> None:
        super().__init__()
        self.void = Void(self.window.rect)
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.0, loop = True)

        self.character = Character()
        self.mouse_pos = (0, 0)

        self.bullet_list = BulletList()
        self.emitter = BulletEmitter(self.window.center, self.bullet_list, RainbowBullet)

        self.emitter.set_pattern(PATTERNS["chaos"])

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        angle = Vec2.from_heading(random() * math.tau)
        self.bullet_list.spawn_bullet(Bullet, self.mouse_pos, angle)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_pos = (x, y)
        # v = Vec2(x, y) - self.emitter.sprite.position
        # self.emitter.direction = v.heading()

    def on_update(self, delta_time: float) -> None:
        self.character.update(delta_time, Vec2(*self.mouse_pos))
        self.bullet_list.update(delta_time)
        self.emitter.update(delta_time)

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        self.emitter.draw()
        self.bullet_list.draw()

        self.character.draw()
