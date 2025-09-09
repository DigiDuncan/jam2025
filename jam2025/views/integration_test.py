from arcade import View, Vec2, LBWH

from jam2025.core.game.bullet import PATTERNS, BulletEmitter, BulletList, RainbowBullet
from jam2025.core.game.character import Character

from jam2025.core.void import Void
from jam2025.data.loading import load_music
from jam2025.core.webcam import WebcamController

from jam2025.core.settings import settings

PLAYER_MAX_HEALTH = 100

class IntegrationTestView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.void = Void(self.window.rect)
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.05, loop = True)

        self.character = Character()

        self.bullet_list = BulletList()
        self.emitter = BulletEmitter(self.window.center, self.bullet_list, RainbowBullet)

        self.emitter.set_pattern(PATTERNS["fourwayspin"])

        self.webcam = WebcamController(settings.webcam_id, settings.webcam_name, region=self.window.rect, bounds=LBWH(0.9, 0.1, -0.8, 0.8))
        self.webcam.debug = True
        self.webcam.sprite.size = self.size
        self.webcam.sprite.position = self.center

    def reset(self) -> None:
        self.player.seek(0.0)
        self.character.reset()

        self.bullet_list = BulletList()
        self.emitter = BulletEmitter(self.window.center, self.bullet_list, RainbowBullet)

        self.emitter.set_pattern(PATTERNS["fourwayspin"])

    def on_update(self, delta_time: float) -> bool | None:
        if self.webcam.webcam.connected:
            self.webcam.update(delta_time)
            self.character.update(delta_time, Vec2(*self.webcam.mapped_cursor))
        else:
            self.character.update(delta_time, Vec2(*self.center))
        self.bullet_list.update(delta_time, self.character)
        self.emitter.update(delta_time)

        if self.character.health <= 0:
            self.reset()

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        if self.webcam.webcam.connected:
            self.webcam.draw()

        self.bullet_list.draw()
        self.emitter.draw()
        self.character.draw()
