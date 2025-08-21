from arcade import XYWH, Text, Vec2, View
from arcade.clock import GLOBAL_CLOCK
import arcade.color

from jam2025.core.ui.button import ClickButton
from jam2025.core.ui.popup import Popup
from jam2025.core.ui.textbox import TobyScriptTextbox
from jam2025.core.void import Void
from jam2025.data.loading import load_music, load_sound
from jam2025.lib.anim import lerp, perc
from jam2025.lib.logging import logger
from jam2025.core.webcam import WebcamController
from jam2025.lib.typing import FOREVER

class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()
        self.void = Void()
        self.music = load_music("found-in-space-17")
        self.player = self.music.play(volume = 0.0, loop = True)

        self.webcam = WebcamController(0)
        self.webcam.sprite.size = (self.size[0] / 2, self.size[1] / 2)
        self.webcam.sprite.center_x = self.center_x
        self.webcam.sprite.top = self.window.rect.top - 100

        popup_rect = XYWH(self.center_x, self.center_y, 128, 128)
        self.popup = Popup(popup_rect, fade_in = 1.0, hold = 3.0, fade_out = 1.0)
        self.popup.popup("mouse")

        self.button = ClickButton(self.center_x, self.height / 4, 40, 5, callback = self.button_clicked)
        self.confirm_label = Text("Confirm", self.center_x, self.button.y + (self.button.size / 2) + 5, font_size = 11, font_name = "GohuFont 11 Nerd Font Mono", anchor_x = "center", align = "center")
        self.mouse_click = False

        beep = load_sound("ut_txt")
        self.textbox = TobyScriptTextbox(XYWH(self.center_x, self.center_y, 500, 100), 22, "GohuFont 11 Nerd Font Mono", cps = 20, beep = beep)

        self.show_self = False
        self.dialouge_shown = 0
        self.dialouge_times = {}
        self.time_since_shown_cam = FOREVER

        self.start_time = GLOBAL_CLOCK.time

    def button_clicked(self) -> None:
        if self.dialouge_shown == 0:
            self.textbox.show(R"\WARE YOU PREPARED TO BE \YSEEN\W?/")
            self.dialouge_times[1] = GLOBAL_CLOCK.time
            self.dialouge_shown += 1
        elif self.dialouge_shown == 1:
            self.textbox.show(R"\WYOUR WEBCAM WILL NOW ACTIVATE.^2&CONTINUE?/")
            self.dialouge_times[2] = GLOBAL_CLOCK.time
            self.dialouge_shown += 1
        elif self.dialouge_shown == 2:
            self.textbox.show("")
            self.show_self = True
            self.button.disabled = True
            self.dialouge_times[3] = GLOBAL_CLOCK.time
            self.dialouge_shown += 1

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.mouse_click = True
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.mouse_click = False
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_update(self, delta_time: float) -> None:
        self.webcam.update(delta_time)
        self.textbox.update(delta_time)

        self.player.volume = lerp(0, 0.15, perc(self.start_time + 1, self.start_time + 3, GLOBAL_CLOCK.time))

        if 1 in self.dialouge_times:
            confirm_alpha = lerp(0, 255, perc(self.dialouge_times[1] + (len(self.textbox.current_message) * self.textbox.spc), self.dialouge_times[1] + (len(self.textbox.current_message) * self.textbox.spc + 1), GLOBAL_CLOCK.time))
            self.confirm_label.color = arcade.color.WHITE.replace(a = int(confirm_alpha))

        if 2 in self.dialouge_times:
            confirm_alpha = lerp(0, 255, perc(self.dialouge_times[2] + (len(self.textbox.current_message) * self.textbox.spc), self.dialouge_times[2] + (len(self.textbox.current_message) * self.textbox.spc + 1), GLOBAL_CLOCK.time))
            self.confirm_label.color = arcade.color.WHITE.replace(a = int(confirm_alpha))

        if 3 in self.dialouge_times:
            webcam_alpha = lerp(0, 255, perc(self.dialouge_times[3], self.dialouge_times[3] + 1, GLOBAL_CLOCK.time))
            self.webcam.sprite.alpha = int(webcam_alpha)

    def on_close(self) -> None:
        self.webcam.webcam.disconnect(block=True)
        logger.debug('closing')

    def on_draw(self) -> bool | None:
        self.clear()
        self.void.draw()
        self.popup.draw()
        self.button.draw()
        self.textbox.draw()

        if self.dialouge_shown in [1, 2]:
            self.confirm_label.draw()

        if self.show_self:
            self.webcam.draw()
