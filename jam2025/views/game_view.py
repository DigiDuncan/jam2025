from arcade import Sprite, Text, View, Vec2, LBWH
import arcade
from arcade.clock import GLOBAL_CLOCK
from arcade.experimental.bloom_filter import BloomFilter

from jam2025.core.game.character import Character
from jam2025.core.game.constants import WAVES
from jam2025.core.game.score_tracker import ScoreTracker
from jam2025.core.game.wave import BossWave, WavePlayer
from jam2025.core.ui.bar import HealthBar, WaveBar
from jam2025.core.ui.button import HoverButton
from jam2025.core.void import Void
from jam2025.data.loading import load_music, load_sprite, load_texture
from jam2025.core.webcam import WebcamController, Webcam

from jam2025.core.settings import settings
from jam2025.lib.anim import ease_linear, perc
from jam2025.lib.frame import Frame, FrameConfig, TextureConfig, Bloom

MAX_SPOTLIGHT_SCALE = 4
MIN_SPOTLIGHT_SCALE = 2

class GameView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.void = Void(self.window.rect)
        self.show_void = True

        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.05, loop = True)

        self.character = Character()
        self.character.position = Vec2(0, 0)

        self.health_bar = HealthBar(self.window.rect.top_right - Vec2(10, 10))
        self.wave_bar = WaveBar(Vec2(0, 0))
        self.wave_bar.position = self.window.rect.top_center + Vec2(self.wave_bar.middle_sprite.width / 2, -10)
        self.wave_text = Text("0", self.wave_bar.middle_sprite.center_x, self.wave_bar.middle_sprite.center_y, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "center", anchor_x = "center", align = "center")

        self.score_tracker = ScoreTracker()
        self.score_tracker.kill_mult = 5

        waves = [WAVES["rectangle"], WAVES["left_and_right"], WAVES["rectangle"], WAVES["left_and_right"], WAVES["boss"]]
        self.wave_player = WavePlayer(waves, self.character, self.score_tracker)

        if settings.has_webcam:
            webcam = settings.connected_webcam
        else:
            webcam = Webcam(settings.webcam_id)
            settings.connected_webcam = webcam
        self.webcam = WebcamController(settings.connected_webcam, settings.webcam_name, region=self.window.rect, bounds=LBWH(0.9, 0.1, -0.8, 0.8))
        self.webcam.sprite.size = self.size
        self.webcam.sprite.position = self.center
        self.webcam.sprite.alpha = 128
        self.show_webcam = False

        self.webcam_on_sprite = load_sprite("webcam")
        self.webcam_on_sprite.right = self.window.rect.right
        self.webcam_on_sprite.bottom = self.window.rect.bottom

        self.use_mouse = False
        self.mouse_pos = self.center

        self.score_text = Text("Score: 0", 5, self.height - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.controls_text = Text("[M]: Use Mouse\n[R]: Reset\n[D]: Debug Overlay\n[Numpad *]: Heal\n[S]Spotlight\n[B] Bloom\n[W] Webcam\n[F] Show FPS\n[V] Show Void", 5, 5,
                                  font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "bottom",
                                  multiline = True, width = int(self.width / 4))

        self.fps_text = Text("FPS 0", 5, self.score_text.bottom - 5, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top")
        self.show_fps = False

        spotlight_texture = load_texture("spotlight")
        self.spotlight = Sprite(spotlight_texture)
        self.show_spotlight = True

        self.bloom_on = True
        self.post_processing = Frame(FrameConfig(self.size, self.size, self.center, TextureConfig()), self.window.ctx)
        self.post_processing.add_process(Bloom(self.size, 3, self.window.ctx))

        self.bloom = 5.0
        self.bloom_filter = BloomFilter(int(self.width), int(self.height), self.bloom)

        self.game_over = False

        self.gameover_text = Text("GAME OVER", self.center_x, self.height * 0.66, font_size = 88, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "center", anchor_x = "center", align = "center")
        self.finalscore_text = Text("SCORE: X", self.center_x, self.height * 0.5, font_size = 44, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "top", anchor_x = "center", align = "center")
        self.game_over_button = HoverButton(self.center_x, self.height * 0.33, 40, 5, callback = self.reset_on_game_over)

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
        elif symbol == arcade.key.S:
            self.show_spotlight = not self.show_spotlight
        elif symbol == arcade.key.A:
            arcade.get_window().ctx.default_atlas.save("./atlas.png")
        elif symbol == arcade.key.B:
            self.bloom_on = not self.bloom_on
        elif symbol == arcade.key.W:
            self.show_webcam = not self.show_webcam
        elif symbol == arcade.key.F:
            self.show_fps = not self.show_fps
        elif symbol == arcade.key.V:
            self.show_void = not self.show_void

    def reset(self) -> None:
        self.player.seek(0.0)
        self.character.reset()
        self.score_tracker.reset()
        self.wave_player.reset()
        self.wave_player.start()
        self.game_over = False
        self.player.play()

    def on_show_view(self) -> None:
        self.wave_player.start()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_pos = (x, y)

    def reset_on_game_over(self) -> None:
        if self.game_over:
            self.reset()

    def on_update(self, delta_time: float) -> bool | None:
        if self.game_over:
            if self.use_mouse:
                self.game_over_button.update(delta_time, self.mouse_pos)
            else:
                self.game_over_button.update(delta_time, self.webcam.mapped_cursor)
            return
        if self.webcam.webcam.connected and not self.use_mouse:
            self.webcam.update(delta_time)
            self.character.update(delta_time, Vec2(*self.webcam.mapped_cursor if self.webcam.mapped_cursor else (0, 0))) if not self.use_mouse else self.character.update(delta_time, Vec2(*self.mouse_pos))
        else:
            self.character.update(delta_time, Vec2(*self.center)) if not self.use_mouse else self.character.update(delta_time, Vec2(*self.mouse_pos))

        self.wave_player.update(delta_time)
        if isinstance(self.wave_player.current_wave, BossWave):
            self.wave_bar.percentage = 1 - perc(0, self.wave_player.current_wave.bullets_needed, self.wave_player.score_tracker.kills_per_wave[self.wave_player.score_tracker.wave])
            self.wave_text.text = f"{self.wave_player.current_wave.bullets_needed - self.wave_player.score_tracker.kills_per_wave[self.wave_player.score_tracker.wave]}"
        else:
            self.wave_bar.percentage = perc(self.wave_player.current_wave_start_time, self.wave_player.current_wave_start_time + self.wave_player.current_wave.total_time, GLOBAL_CLOCK.time)
            self.wave_text.text = f"WAVE {self.wave_player.wave_count}"

        self.health_bar.percentage = (self.character.health / self.character.max_health)
        self.score_text.text = f"Score: {self.score_tracker.score}"
        self.finalscore_text.text = f"SCORE: {self.score_tracker.score}"

        self.spotlight.position = self.character.position
        self.spotlight.scale = ease_linear(MIN_SPOTLIGHT_SCALE, MAX_SPOTLIGHT_SCALE, self.health_bar.percentage)

        self.fps_text.text = f"FPS {1/delta_time:.1f}"

        if self.character.health <= 0:
            self.player.pause()
            self.game_over = True

    def on_draw(self) -> bool | None:
        self.clear()
        self.window.use()
        if self.bloom_on:
            self.draw_bloomed()
        else:
            self.draw_basic()

        if self.show_spotlight:
            arcade.draw_sprite(self.spotlight)
            if settings.debug:
                self.wave_player.draw()

        if self.webcam.webcam.connected and not self.use_mouse:
            arcade.draw_sprite(self.webcam_on_sprite)

        self.health_bar.draw()
        self.score_text.draw()
        # self.controls_text.draw()
        self.wave_bar.draw()
        self.wave_text.draw()

        if self.game_over:
            arcade.draw_rect_filled(self.window.rect, arcade.color.BURGUNDY)
            self.gameover_text.draw()
            self.finalscore_text.draw()
            self.game_over_button.draw()
            if self.use_mouse:
                arcade.draw_circle_filled(*self.mouse_pos, 10, arcade.color.WHITE)
            else:
                arcade.draw_circle_filled(*self.webcam.mapped_cursor, 10, arcade.color.WHITE)

        if self.show_fps:
            self.fps_text.draw()

    def draw_basic(self) -> None:
        if self.show_void:
            self.void.draw()
        if self.webcam.webcam.connected and self.show_webcam:
            self.webcam.draw()
        self.wave_player.draw()

    def draw_bloomed(self) -> None:
        with self.post_processing.capture_unprocessed((0, 0, 0, 0)):
            if self.show_void:
                self.void.draw()
            if self.webcam.webcam.connected and self.show_webcam:
                self.webcam.draw()
        with self.post_processing:
            self.wave_player.draw()
        self.post_processing.render()
