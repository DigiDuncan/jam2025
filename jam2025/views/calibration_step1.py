from arcade import XYWH, View, Window

from jam2025.core.popup import Popup


class MouseCalibrationView(View):
    def __init__(self) -> None:
        super().__init__()

        popup_rect = XYWH(self.center_x, self.center_y, 100, 100)
        self.popup = Popup(popup_rect)
        self.popup.popup()

    def on_draw(self) -> bool | None:
        self.clear()
        self.popup.draw()
