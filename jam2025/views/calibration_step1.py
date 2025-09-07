from enum import IntEnum

from arcade import LBWH, XYWH, Text, Vec2, View
from arcade.clock import GLOBAL_CLOCK
import arcade.color

from jam2025.core.ui.button import ClickButton
from jam2025.core.ui.popup import Popup
from jam2025.core.ui.slider import Slider
from jam2025.core.ui.textbox import TobyScriptTextbox
from jam2025.core.void import Void
from jam2025.data.loading import load_music, load_sound
from jam2025.lib.anim import ease_quadinout, ease_quadout, lerp, perc
from jam2025.lib.logging import logger
from jam2025.core.webcam import WebcamController
from jam2025.lib.typing import FOREVER
from jam2025.core.settings import SETTINGS
from jam2025.lib.utils import open_settings

class Phase(IntEnum):
    NONE = 0
    BE_SEEN = 1
    WEBCAM_ACTIVATE = 2
    WEBCAM_ON = 3
    SHOW_CALIB = 4
    HIDE_CALIB = 5

def make_text(text: str, x: float, y: float, align: str = "left") -> Text:
    return Text(text, x, y, font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_x = align, align = align)

class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()
        self.void = Void(self.window.rect)
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.0, loop = True)

        self.webcam = WebcamController(0)
        self.webcam.sprite.size = (self.size[0] / 2, self.size[1] / 2)
        self.webcam.sprite.center_x = self.center_x
        self.webcam.sprite.top = self.window.rect.top - 100

        popup_rect = XYWH(self.center_x, self.center_y, 128, 128)
        self.popup = Popup(popup_rect, fade_in = 1.0, hold = 3.0, fade_out = 1.0)
        self.popup.popup("mouse")

        self.button = ClickButton(self.center_x, self.height / 6, 40, 5, callback = self.button_clicked)
        self.confirm_label = make_text("Confirm", self.center_x, self.button.y + (self.button.size / 2) + 5, align = "center")
        self.confirm_delays = {1: 0, 2: 1, 3: 2, 4: 2}

        self.mouse_click = False

        beep = load_sound("ut_txt")
        self.textbox = TobyScriptTextbox(XYWH(self.center_x, self.center_y, 500, 100), 22, "GohuFont 11 Nerd Font Mono", cps = 20, beep = beep)

        threshold_rect = LBWH(self.width - 550, self.center_y + 75, 500, 50)
        self.threshold_slider = Slider[int](threshold_rect, 1, 255, rounding_function = int)
        self.threshold_slider.value = 245
        self.threshold_label = make_text("Threshold: 245", self.threshold_slider.rect.left, self.threshold_slider.rect.top + 5)
        self.threshold_slider.register(self.update_threshold)

        downsample_rect = LBWH(self.width - 550, self.center_y - 25, 500, 50)
        self.downsample_slider = Slider[int](downsample_rect, 4, 8, rounding_function = int)
        self.downsample_slider.value = 8
        self.downsample_label = make_text("Downsample: 8x", self.downsample_slider.rect.left, self.downsample_slider.rect.top + 5)
        self.downsample_slider.register(self.update_downsample)

        polled_points_rect = LBWH(self.width - 550, self.center_y - 125, 500, 50)
        self.polled_points_slider = Slider[int](polled_points_rect, 1, 500, rounding_function = int)
        self.polled_points_slider.value = 50
        self.polled_points_label = make_text("Polled Points: 50", self.polled_points_slider.rect.left, self.polled_points_slider.rect.top + 5)
        self.polled_points_slider.register(self.update_polled_points)

        self.show_self = False
        self.phase = 0
        self.dialouge_times = {}
        self.time_since_shown_cam = FOREVER

        self.start_time = GLOBAL_CLOCK.time

    @property
    def text_time(self) -> float:
         return len(self.textbox.current_message) * self.textbox.spc

    def button_clicked(self) -> None:
        self.phase += 1
        self.dialouge_times[self.phase] = GLOBAL_CLOCK.time

        if self.phase == Phase.BE_SEEN:
            self.textbox.show(R"\WARE YOU PREPARED TO BE \YSEEN\W?/")
        elif self.phase == Phase.WEBCAM_ACTIVATE:
            self.textbox.show(R"\WYOUR WEBCAM WILL NOW ACTIVATE.^2&CONTINUE?/")
        elif self.phase == Phase.WEBCAM_ON:
            self.textbox.show("")
            self.show_self = True
            self.confirm_label.text = "Continue"
        elif self.phase == Phase.SHOW_CALIB:
            ...
        elif self.phase == Phase.HIDE_CALIB:
            self.show_self = False
            self.popup.popup("no_mouse")
            self.button.disabled = True

    def update_threshold(self, val: int) -> None:
        self.threshold_label.text = f"Threshold: {val}"
        SETTINGS.threshold = val

    def update_downsample(self, val: int) -> None:
        self.downsample_label.text = f"Downsample: {val}"
        SETTINGS.downsample = val

    def update_polled_points(self, val: int) -> None:
        self.polled_points_label.text = f"Polled Points: {val}"
        SETTINGS.polled_points = val

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.mouse_click = True
        self.button.update(Vec2(x, y), self.mouse_click)
        self.threshold_slider.update(Vec2(x, y))
        self.downsample_slider.update(Vec2(x, y))
        self.polled_points_slider.update(Vec2(x, y))

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.mouse_click = False
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, _buttons: int, _modifiers: int) -> bool | None:
        self.threshold_slider.update(Vec2(x, y))
        self.downsample_slider.update(Vec2(x, y))
        self.polled_points_slider.update(Vec2(x, y))

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.S:
            open_settings(SETTINGS.device_name)

    def on_update(self, delta_time: float) -> None:
        self.webcam.update(delta_time)
        self.textbox.update(delta_time)

        self.player.volume = lerp(0, 0.15, perc(self.start_time + 1, self.start_time + 3, GLOBAL_CLOCK.time))

        if self.phase == Phase.NONE:
            self.button.disabled = self.popup.on_screen

        if self.phase in [Phase.BE_SEEN, Phase.WEBCAM_ACTIVATE, Phase.WEBCAM_ON, Phase.SHOW_CALIB]:
            confirm_alpha = lerp(0, 255,
                                 perc(self.dialouge_times[self.phase] + self.text_time + self.confirm_delays[self.phase],
                                      self.dialouge_times[self.phase] + self.text_time + self.confirm_delays[self.phase] + 1,
                                      GLOBAL_CLOCK.time))
            self.confirm_label.color = arcade.color.WHITE.replace(a = int(confirm_alpha))

        if Phase.WEBCAM_ON in self.dialouge_times:
            webcam_alpha = lerp(0, 255, perc(self.dialouge_times[Phase.WEBCAM_ON], self.dialouge_times[Phase.WEBCAM_ON] + 1, GLOBAL_CLOCK.time))
            self.webcam.sprite.alpha = int(webcam_alpha)

        # (640.0, 440.0)
        if Phase.SHOW_CALIB in self.dialouge_times:
            self.webcam.sprite.position = (
                ease_quadinout(640.0, (self.webcam.sprite.width / 2) + 10, perc(self.dialouge_times[Phase.SHOW_CALIB], self.dialouge_times[Phase.SHOW_CALIB] + 1, GLOBAL_CLOCK.time)),
                ease_quadinout(440.0, self.center_y, perc(self.dialouge_times[Phase.SHOW_CALIB], self.dialouge_times[Phase.SHOW_CALIB] + 1, GLOBAL_CLOCK.time))
            )
            self.webcam.debug = True

            for slider, text in zip([self.threshold_slider, self.downsample_slider, self.polled_points_slider], [self.threshold_label, self.downsample_label, self.polled_points_label], strict = True):
                x = ease_quadout(self.width, self.width - 550, perc(self.dialouge_times[Phase.SHOW_CALIB], self.dialouge_times[Phase.SHOW_CALIB] + 1, GLOBAL_CLOCK.time))
                slider.rect = slider.rect.align_left(x)
                text.x = slider.rect.left

    def on_close(self) -> None:
        self.webcam.webcam.disconnect(block=True)
        logger.debug('closing')

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        self.popup.draw()
        self.button.draw()
        self.textbox.draw()

        if self.phase in [Phase.BE_SEEN, Phase.WEBCAM_ACTIVATE, Phase.WEBCAM_ON, Phase.SHOW_CALIB]:
            self.confirm_label.draw()

        if self.phase in [Phase.SHOW_CALIB]:
            self.threshold_slider.draw()
            self.downsample_slider.draw()
            self.polled_points_slider.draw()
            self.threshold_label.draw()
            self.downsample_label.draw()
            self.polled_points_label.draw()

        if self.show_self:
            self.webcam.draw()
