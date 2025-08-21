from arcade import XYWH, Vec2, View

from jam2025.core.popup import Popup
from jam2025.core.slider import Slider
from jam2025.core.webcam import get_available_cameras


class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()

        popup_rect = XYWH(self.center_x, self.center_y, 75, 75)
        popup_rect = popup_rect.align_right(self.width - 25)
        popup_rect = popup_rect.align_bottom(25)
        self.popup = Popup(popup_rect, fade_in = 1.0, hold = 3.0, fade_out = 1.0)
        self.popup.popup("mouse")

        self.slider = Slider[float](XYWH(self.center_x, self.center_y, 500, 50))

        self.cameras = get_available_cameras()
        print(self.cameras)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, _buttons: int, _modifiers: int) -> bool | None:
        print("wee")
        self.slider.update(Vec2(x, y))

    def on_draw(self) -> bool | None:
        self.clear()
        self.popup.draw()
        self.slider.draw()
