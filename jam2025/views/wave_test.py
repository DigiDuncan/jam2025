from arcade import SpriteCircle, Text, View, Vec2, LBWH
import arcade

from jam2025.core.game.bullet import PATTERNS, BulletEmitter, BulletList, RainbowBullet, SpinningBulletEmitter
from jam2025.core.game.character import Character
from jam2025.core.game.enemy import Enemy
from jam2025.core.game.score_tracker import ScoreTracker
from jam2025.core.game.wave import Keyframe, MotionPath, Wave, WavePlayer
from jam2025.core.ui.bar import HealthBar
from jam2025.core.void import Void
from jam2025.data.loading import load_music
from jam2025.core.webcam import WebcamController

from jam2025.core.settings import settings

dummy_bullet_list = BulletList()

class WaveTestView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.void = Void(self.window.rect)
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.05, loop = True)

        self.character = Character()
        self.character.position = Vec2(0, 0)

        self.health_bar = HealthBar(self.window.rect.top_right - Vec2(10, 10))
        self.score_tracker = ScoreTracker()
        self.score_tracker.kill_mult = 5

        WAVES = [
            Wave(10, [
                MotionPath(Enemy(SpriteCircle(10, arcade.color.WHITE),
                                 SpinningBulletEmitter((640, 480),
                                                       dummy_bullet_list,
                                                       RainbowBullet,
                                                       PATTERNS["fourway"])),
                        [Keyframe(0, (1280 * 0.25, 720 * 0.25)),
                        Keyframe(2, (1280 * 0.75, 720 * 0.25)),
                        Keyframe(4, (1280 * 0.75, 720 * 0.75)),
                        Keyframe(6, (1280 * 0.25, 720 * 0.75))])
            ])
        ]

        self.wave_player = WavePlayer(WAVES, self.character, self.score_tracker)

        self.webcam = WebcamController(settings.webcam_id, settings.webcam_name, region=self.window.rect, bounds=LBWH(0.9, 0.1, -0.8, 0.8))
        self.webcam.sprite.size = self.size
        self.webcam.sprite.position = self.center
        self.webcam.sprite.alpha = 128

        self.use_mouse = False
        self.mouse_pos = self.center

        self.score_text = Text("Score: 0", 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.controls_text = Text("[M]: Use Mouse\n[R]: Reset\n[D]: Debug Overlay\n[Numpad *]: Heal", 5, 5,
                                  font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "bottom",
                                  multiline = True, width = int(self.width / 4))

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.M:
            self.use_mouse = not self.use_mouse
            self.window.set_mouse_visible(not self.use_mouse)
        elif symbol == arcade.key.D:
            settings.debug = not settings.debug
        elif symbol == arcade.key.NUM_MULTIPLY:
            self.character.health = self.character.max_health
        elif symbol == arcade.key.R:
            self.reset()

    def reset(self) -> None:
        self.player.seek(0.0)
        self.character.reset()
        self.wave_player.reset()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_pos = (x, y)

    def on_update(self, delta_time: float) -> bool | None:
        if self.webcam.webcam.connected:
            self.webcam.update(delta_time)
            self.character.update(delta_time, Vec2(*self.webcam.mapped_cursor if self.webcam.mapped_cursor else (0, 0))) if not self.use_mouse else self.character.update(delta_time, Vec2(*self.mouse_pos))
        else:
            self.character.update(delta_time, Vec2(*self.center)) if not self.use_mouse else self.character.update(delta_time, Vec2(*self.mouse_pos))

        self.wave_player.update(delta_time)

        self.health_bar.percentage = (self.character.health / self.character.max_health)
        self.score_text.text = f"Score: {self.score_tracker.score}"

        if self.character.health <= 0:
            self.reset()

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        if self.webcam.webcam.connected:
            self.webcam.draw()

        self.wave_player.draw()

        self.health_bar.draw()
        self.score_text.draw()
        self.controls_text.draw()
