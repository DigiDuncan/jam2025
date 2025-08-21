from arcade import XYWH, Text, Vec2, View
import arcade

from jam2025.core.ui.button import ClickButton
from jam2025.core.ui.popup import Popup
from jam2025.core.ui.slider import Slider
from jam2025.lib.logging import logger
from jam2025.core.webcam import WebcamController

class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()
        self.webcam = WebcamController(0)
        self.webcam.sprite.size = (self.size[0] / 2, self.size[1] / 2)
        self.webcam.sprite.center_x = self.center_x
        self.webcam.sprite.top = self.window.rect.top - 10

        popup_rect = XYWH(self.center_x, self.center_y, 75, 75)
        popup_rect = popup_rect.align_right(self.width - 25)
        popup_rect = popup_rect.align_bottom(25)
        self.popup = Popup(popup_rect, fade_in = 1.0, hold = 3.0, fade_out = 1.0)
        self.popup.popup("mouse")

        self.slider = Slider[float](XYWH(self.center_x, self.center_y - 100, 500, 50))
        self.slider.register(self.update_slider_text)
        self.slider_text = Text("0.0", self.slider.rect.left, self.slider.rect.top, font_size = 22, font_name = "GohuFont 11 Nerd Font Mono", anchor_y = "bottom")

        self.button = ClickButton(self.center_x, self.height / 4, 40, 5)
        self.mouse_click = False

    def update_slider_text(self, value: float) -> None:
        self.slider_text.text = f"{value:.1f}"

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            if Vec2(x, y) in self.slider.handle_rect:
                self.slider.grabbed = True
        self.mouse_click = True
        self.button.update(Vec2(x, y), self.mouse_click)
        self.slider.update(Vec2(x, y))

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.slider.grabbed = False
        self.mouse_click = False
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, _buttons: int, _modifiers: int) -> bool | None:
        self.slider.update(Vec2(x, y))

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.button.update(Vec2(x, y), self.mouse_click)

    def on_update(self, delta_time: float) -> None:
        self.webcam.update(delta_time)

    def on_close(self) -> None:
        self.webcam.webcam.disconnect(block=True)
        logger.debug('closing')

    def on_draw(self) -> bool | None:
        self.clear()
        self.popup.draw()
        self.slider.draw()
        self.slider_text.draw()
        self.button.draw()
        self.webcam.draw()
