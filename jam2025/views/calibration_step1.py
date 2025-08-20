from arcade import XYWH, View

from jam2025.core.popup import Popup


class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()

        popup_rect = XYWH(self.center_x, self.center_y, 75, 75)
        popup_rect = popup_rect.align_right(self.width - 25)
        popup_rect = popup_rect.align_bottom(25)
        self.popup = Popup(popup_rect, fade_in = 1.0, hold = 3.0, fade_out = 1.0)
        self.popup.popup("mouse")

    def on_draw(self) -> bool | None:
        self.clear()
        self.popup.draw()
